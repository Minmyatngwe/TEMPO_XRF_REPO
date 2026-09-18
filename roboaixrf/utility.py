import time
while True:
    with open("/home/user/persistent/xrftest/TEMPO_XRF_REPO/python_code/roboai_xrf_frontend/tqdm_output.txt", "r") as f:
        print(f.read())


        time.sleep(2)  # Add a small delay to allow the file to be written