import logging 
import socket
import subprocess

def get_logger(name: str) -> logging.Logger:
    # function to get python logger 

    return logging.getLogger(f"[{socket.gethostname()}] {name}")


def run_shell_command(cmd: str) -> str:
    # To run shell commands and return their output as a string

    return subprocess.run(cmd, text=True, shell=True, check=True, capture_output=True).stdout