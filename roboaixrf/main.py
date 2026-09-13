
from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import numpy as np
import plotly.graph_objects as go
import subprocess

from pydantic import BaseModel, PrivateAttr

from .config.xrfconfig import XRFConfigure
from .config.write_json import write_json
from .detector_noise.xray_tube import get_flu
from .detector_noise.pipeline import apply_detectornoise
from plotly.subplots import make_subplots


class RoboAiXrfSimulation(BaseModel):
    """
    RoboAI XRF simulation controller.

    Workflow
    --------
    1. compile()
       - Build the SpekPy source spectrum at 1 mAs.
       - Write the Geant4 JSON configuration.

    2. run()
       - Run Geant4 with the source spectrum.
       - Estimate detector yield per simulated primary photon.

    3. detector_noise()
       - User chooses current and live time.
       - Re-run SpekPy fluence calculation using:
             mAs = current_mA * live_time_s
       - Convert fluence to physical photons through the tube collimator.
       - Scale the Geant4 response.
       - Apply arrival-time sampling, pile-up, and detector broadening.
    """

    config: XRFConfigure
    config_path: Path

    # Internal package path; this is not part of the user's simulation config.
    ROOTPATH: ClassVar[Path] = Path(__file__).resolve().parent

    _beam_on: int = PrivateAttr(default=0)
    _is_compiled: bool = PrivateAttr(default=False)

    _energy_bin: np.ndarray | None = PrivateAttr(default=None)
    _fluence_list: np.ndarray | None = PrivateAttr(default=None)

    _last_mas: float | None = PrivateAttr(default=None)
    _last_incident_photons: float | None = PrivateAttr(default=None)

    @property
    def is_compiled(self) -> bool:
        return self._is_compiled

    @property
    def beam_on(self) -> int:
        return self._beam_on

    @property
    def energy_bin(self) -> np.ndarray | None:
        return self._energy_bin

    @property
    def fluence_list(self) -> np.ndarray | None:
        return self._fluence_list

    @property
    def last_mas(self) -> float | None:
        return self._last_mas

    @property
    def last_incident_photons(self) -> float | None:
        return self._last_incident_photons

    def model_post_init(self, __context) -> None:
        self.config.validate_complete()

        self.config_path = self.config_path.resolve()
        self.config_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _get_tube_spekpy_inputs(self):
        """
        Collect the tube values needed by SpekPy.

        Returns
        -------
        tube
            X-ray tube configuration.
        filters
            SpekPy filter dictionaries.
        source_to_collimator_mm
            Focal-spot-to-virtual-collimator distance in mm.
        """
        tube = self.config.xray_tube

        if tube is None:
            raise ValueError("X-ray tube configuration is missing.")

        filters = [
            f.model_dump()
            for f in tube.tube_filter_spekpy
        ]

        source_to_sample_mm = tube.placement.position.distance_mm

        window_to_sample_mm = tube.tube_window_to_sample_distance_mm
    
        window_to_collimator_mm = tube.tube_window_to_virtual_collimator_distance_mm

        tube_internal_length_mm = source_to_sample_mm- window_to_sample_mm


        if tube_internal_length_mm < 0:
            raise ValueError(
                "Focal-spot-to-sample distance cannot be smaller "
                "than tube-window-to-sample distance."
            )

        source_to_collimator_mm = tube_internal_length_mm+ window_to_collimator_mm
        

        if source_to_collimator_mm <= 0:
            raise ValueError(
                "Focal-spot-to-collimator distance must be greater than 0."
            )

        return tube, filters, source_to_collimator_mm

    def write_spectrum_plot( self,energy_mev: np.ndarray, count: np.ndarray) -> Path:
        """
        Write the source spectrum used by Geant4 for the browser visualizer.

        Parameters
        ----------
        energy_mev
            Source energy bins in MeV.
        count
            Relative SpekPy fluence weights.
        """
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=energy_mev * 1000.0,
                y=count,
                mode="lines",
                name="X-ray tube spectrum",
            )
        )

        fig.update_layout(
            title="X-ray Tube Spectrum",
            xaxis_title="Energy (keV)",
            yaxis_title="Relative fluence",
            template="plotly_white",
        )

        output_file = (
            self.ROOTPATH
            / "vis"
            / "public"
            / "runs"
            / "spectrum.json"
        )

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file.write_text(
            fig.to_json(),
            encoding="utf-8",
        )

        return output_file

    def write_macro(self,beam_on: int,number_of_thread: int,print_display: int,) -> tuple[str, Path]:
        if not self.is_compiled:
            raise RuntimeError("Call simulation.compile() first.")

        if self._energy_bin is None or self._fluence_list is None:
            raise RuntimeError(
                "Source spectrum is missing. Call simulation.compile() first."
            )

        if beam_on <= 0:
            raise ValueError("beam_on must be greater than 0.")

        if number_of_thread <= 0:
            raise ValueError(
                "number_of_thread must be greater than 0."
            )

        if print_display <= 0:
            raise ValueError(
                "print_display must be greater than 0."
            )

        macro_lines = [
            f"/run/numberOfThreads {number_of_thread}",
            "/run/initialize",
            "/gps/particle gamma",
            "/gps/ene/type User",
            "/gps/hist/type energy",
        ]

        # GPS uses these values as relative histogram weights.
        for energy, fluence in zip(self._energy_bin,self._fluence_list):
            macro_lines.append(
                f"/gps/hist/point {energy} {fluence}"
            )

        macro_lines.extend(
            [
                f"/run/printProgress {print_display}",
                f"/run/beamOn {beam_on}",
            ]
        )

        macro_text = "\n".join(macro_lines) + "\n"

        macro_file_path = (
            self.config_path / "run.mac"
        )

        macro_file_path.write_text(
            macro_text,
            encoding="utf-8",
        )
        return macro_text, macro_file_path

    def compile(self) -> None:
        """
        Prepare the source spectrum and Geant4 JSON configuration.

        The source spectrum is generated at 1 mAs because mAs changes
        intensity, not the normalized source-energy shape.

        Actual current/time scaling is done later in detector_noise()
        by calling SpekPy again with the user's requested mAs.
        """
        tube, filters, source_to_collimator_mm = self._get_tube_spekpy_inputs()

        energy_bin_kev,fluence_list, _= get_flu(
                        mas=1.0,
                        voltage=tube.voltage_kv,
                        anode_degree=tube.anode_angle_deg,
                        anode_target_material=tube.anode_symbol,
                        filters=filters,
                        source_to_tube_collimator_mm=source_to_collimator_mm,
                        tube_type=tube.tube_type,
                        target_thickness_um=tube.target_thickness_um,
                    )

        self._energy_bin = np.asarray(
            energy_bin_kev,
            dtype=np.float64,
        ) / 1000.0 

        self._fluence_list = np.asarray(
            fluence_list,
            dtype=np.float64,
        )

        if self._energy_bin.size == 0:
            raise ValueError("SpekPy returned no energy bins.")

        if self._fluence_list.size != self._energy_bin.size:
            raise ValueError(
                "SpekPy energy and fluence arrays have different lengths."
            )

        if not np.all(np.isfinite(self._fluence_list)):
            raise ValueError(
                "SpekPy source spectrum contains non-finite values."
            )

        if np.sum(self._fluence_list) <= 0:
            raise ValueError(
                "SpekPy source spectrum has zero total fluence."
            )

        write_json(
            self.config,
            self.config_path / "config.json",
        )

        self._beam_on = 0
        self._last_mas = None
        self._last_incident_photons = None
        self._is_compiled = True

    def show_vis(self,beam_on: int = 100,number_of_thread: int = 1,) -> None:
        """
        Run a small visualization simulation and launch the Vite viewer.

        This is NOT registered as the quantitative Geant4 response run.
        Call run() afterwards before detector_noise().
        """
        if not self.is_compiled:
            raise RuntimeError(
                "Call simulation.compile() first."
            )

        _, macro_file_path = self.write_macro(
            beam_on=beam_on,
            number_of_thread=number_of_thread,
            print_display=max(1, beam_on),
        )

        self.write_spectrum_plot(
            self._energy_bin,
            self._fluence_list,
        )

        # show_vis() can create/overwrite simulation.root, so invalidate
        # the quantitative response state. The user must call run() next.
        self._beam_on = 0

        subprocess.run(
            [
                "./sim",
                str(self.config_path / "config.json"),
                str(macro_file_path),
            ],
            cwd=(
                self.ROOTPATH.parent
                / "geant4_code"
                / "build"
            ),
            check=True,
        )

        subprocess.Popen(
            [
                "npx",
                "vite",
            ],
            cwd=self.ROOTPATH / "vis",
        )

    def run(self,beam_on: int,number_of_thread: int,print_display: int = 1_000_000,) -> Path:
        """
        Run the quantitative Geant4 response simulation.

        Returns
        -------
        Path
            Path to simulation.root.
        """
        if not self.is_compiled:
            raise RuntimeError(
                "Call simulation.compile() first."
            )

        _, macro_file_path = self.write_macro(
            beam_on=beam_on,
            number_of_thread=number_of_thread,
            print_display=print_display,
        )

        config_file = (
            self.config_path / "config.json"
        )

        root_file = (
            self.config_path / "simulation.root"
        )

        if root_file.exists():
            root_file.unlink()

        self._beam_on = 0

        subprocess.run(
            [
                "./sim",
                str(config_file),
                str(macro_file_path),
            ],
            cwd=(
                self.ROOTPATH.parent
                / "geant4_code"
                / "build"
            ),
            check=True,
        )

        if not root_file.is_file():
            raise RuntimeError(
                "Geant4 finished successfully but simulation.root "
                f"was not created at: {root_file}"
            )

        self._beam_on = beam_on

        return root_file

    def detector_noise(self,*,fwhm: float,fwhm_energy_kev: float,detector_zero_offset: float,detector_gain_kev: float,
                        live_time: float, pile_up_window_us: float,current: float | None = None,fano_factor: float = 0.115,
                        pair_creation_energy_ev: float = 3.6,mca_channels: int = 2048,chunk_size: int = 3_000_000,number_of_buckets: int = 65, ):
        """
        Create the physical detector spectrum for a requested acquisition.

        Important
        ---------
        Current and live time do NOT change the stored Geant4 source shape.
        Instead:

            mAs = current[mA] * live_time[s]

        SpekPy is called again with that mAs to obtain the physical fluence.
        That fluence is multiplied by the tube-collimator area to obtain
        the physical number of incident photons.

        The current defaults to config.xray_tube.current_ma when current=None.
        """
        if not self.is_compiled:
            raise RuntimeError(
                "Call simulation.compile() first."
            )

        if self._beam_on < 2:
            raise RuntimeError(
                "No quantitative Geant4 response run is registered. "
                "Call simulation.run() with beam_on >= 2 first."
            )

        root_file = self.config_path / "simulation.root"
        

        if not root_file.is_file():
            raise FileNotFoundError(
                f"simulation.root not found: {root_file}"
            )

        if live_time <= 0:
            raise ValueError(
                "live_time must be greater than 0 seconds."
            )

        if detector_gain_kev <= 0:
            raise ValueError(
                "detector_gain_kev must be greater than 0."
            )

        if mca_channels <= 0:
            raise ValueError(
                "mca_channels must be greater than 0."
            )

        tube, filters, source_to_collimator_mm = (
            self._get_tube_spekpy_inputs()
        )

        if current is None:
            current = float(tube.current_ma)

        if current <= 0:
            raise ValueError(
                "current must be greater than 0 mA."
            )

        # mA * s = mAs
        mas = current * live_time

        _, _, fluence_photons_cm2 = get_flu(
            mas=mas,
            voltage=tube.voltage_kv,
            anode_degree=tube.anode_angle_deg,
            anode_target_material=tube.anode_symbol,
            filters=filters,
            source_to_tube_collimator_mm=source_to_collimator_mm,
            tube_type=tube.tube_type,
            target_thickness_um=tube.target_thickness_um,
        )

        # Tube-collimator radius is configured in mm.
        # SpekPy fluence is photons/cm², so convert radius to cm.
        radius_cm = (
            tube.tube_collimator_radius_mm / 10.0
        )

        area_cm2 = (
            np.pi * radius_cm**2
        )

        # photons/cm² * cm² = photons
        number_of_photon = (
            float(fluence_photons_cm2)
            * area_cm2
        )

        self._last_mas = mas
        self._last_incident_photons = number_of_photon

        print("\n========== PHYSICAL ACQUISITION ==========")
        print("Current:", current, "mA")
        print("Live time:", live_time, "s")
        print("Exposure:", mas, "mAs")
        print(
            "SpekPy fluence:",
            fluence_photons_cm2,
            "photons/cm²",
        )
        print(
            "Collimator radius:",
            tube.tube_collimator_radius_mm,
            "mm",
        )
        print(
            "Collimator area:",
            area_cm2,
            "cm²",
        )
        print(
            "Physical photons through collimator:",
            number_of_photon,
        )

        (
            final_count,
            final_energy_centers,
            scaled_count,
            average_channel_wise_yield,
            se_channel_wise_yield,
            spectrum_yield_avg,
            spectrum_se,
        ) = apply_detectornoise(
            root_path=root_file,

            # Number of Monte Carlo primary histories used to estimate
            # response/yield.
            beam_on=self._beam_on,

            # Number of real photons for THIS requested acquisition.
            number_of_photon=number_of_photon,

            # Kept separately because event rate/pile-up depends on time.
            live_time=live_time,

            fwhm=fwhm,
            fwhm_energy=fwhm_energy_kev,

            detector_zero_offset=detector_zero_offset,

            # IMPORTANT: this pipeline works in keV.
            # Example: 0.024 means 24 eV/channel.
            detector_gain=detector_gain_kev,

            pile_up_window=pile_up_window_us,

            fano_factor=fano_factor,
            pair_creation_energy_ev=(
                pair_creation_energy_ev
            ),

            mca_channels=mca_channels,
            chunk_size=chunk_size,
            number_of_buckets=number_of_buckets,
        )

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=(
                "Before Detector Noise",
                "After Detector Noise",
            ),
        )

        # -------------------------
        # BEFORE detector noise
        # -------------------------
        fig.add_trace(
            go.Scatter(
                x=final_energy_centers,
                y=scaled_count,
                mode="lines",
                name="Before detector noise",
            ),
            row=1,
            col=1,
        )

        # -------------------------
        # AFTER detector noise
        # -------------------------
        fig.add_trace(
            go.Scatter(
                x=final_energy_centers,
                y=final_count,
                mode="lines",
                name="After detector noise",
            ),
            row=1,
            col=2,
        )

        fig.update_xaxes(
            title_text="Energy (keV)",
            row=1,
            col=1,
        )

        fig.update_xaxes(
            title_text="Energy (keV)",
            row=1,
            col=2,
        )

        fig.update_yaxes(
            title_text="Counts",
            row=1,
            col=1,
        )

        fig.update_yaxes(
            title_text="Counts",
            row=1,
            col=2,
        )

        fig.update_layout(
            title=(
                "XRF Simulated Spectrum "
                f"({current:g} mA, {live_time:g} s)"
            ),
            template="plotly_white",
            height=600,
            width=1500,
        )

        plot_path = (
            self.config_path
            / "simulation_spectrum.html"
        )

        fig.write_html(
            plot_path,
            include_plotlyjs=True,
        )

        print(
            f"Spectrum saved to: {plot_path}"
        )

        return (
            final_count,
            final_energy_centers,
            scaled_count,
            average_channel_wise_yield,
            se_channel_wise_yield,
            spectrum_yield_avg,
            spectrum_se,
        )

if __name__=="__main__":
    pass