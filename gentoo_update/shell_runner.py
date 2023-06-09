import os
import sys
import shlex
import logging
import subprocess
from datetime import datetime

class ShellRunner:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        self.log_dir = "/var/log/gentoo_update"
        self.log_filename = f"{self.log_dir}/log_{self.timestamp}"
        self.logger = self.initiate_logger()

    def initiate_logger(self):
        """
        Create a logger with two handlers:
            1. terminal output
            2. file output
        Both handlers have the same logging level (INFO)
        and share the same formatter.
        Formatters include timestamp, log level and the message.
    
        Returns:
            logging.Logger: Configured logger.
            log_filename: Log filename.
        """
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
    
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
    
        terminal_handler = logging.StreamHandler()
        terminal_handler.setLevel(logging.INFO)
        file_handler = logging.FileHandler(self.log_filename)
        file_handler.setLevel(logging.INFO)
    
        formater = logging.Formatter(
            "[%(asctime)s %(levelname)s] ::: %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
        )
        terminal_handler.setFormatter(formater)
        file_handler.setFormatter(formater)
    
        logger.addHandler(terminal_handler)
        logger.addHandler(file_handler)
    
        return logger


    def run_shell_script(self, *args):
        """
        Run a shell script and stream standard output
        and standard error to terminal and a log file.
    
        Args:
            script_path (str): Shell script path.
            *args (str): Arguments for the shell script.
                         They need to be handled by the script.
        """
        command = shlex.split(f"updater.sh {' '.join(args)}")
        with subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as script_stream:
            # Process stdout
            for line in script_stream.stdout:
                self.logger.info(line.decode().rstrip("\n"))
    
            # Process stderr
            stderr_output = []
            for line in script_stream.stderr:
                line = line.decode().rstrip("\n")
                stderr_output.append(line)
                self.logger.error(line)
    
            script_stream.wait()
    
            if script_stream.returncode != 0:
                error_message = (
                    "updater.sh exited with error code {script_stream.returncode}"
                )
                if stderr_output:
                    stderr_output_message = "n".join(stderr_output)
                    error_message += (
                        f"\nStandard error output:\n{stderr_output_message}"
                    )
                self.logger.error(error_message)
                sys.exit(script_stream.returncode)
        self.logger.info("gentoo_update completed it's tasks!")
        self.logger.info(f"log file can be found at: {self.log_filename}")
