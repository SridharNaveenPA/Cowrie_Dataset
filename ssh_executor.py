import time
import paramiko


class SSHExecutor:

    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.client = None
        self.shell = None

    def connect(self):

        self.client = paramiko.SSHClient()

        self.client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )

        self.client.connect(
            self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            allow_agent=False,
            look_for_keys=False
        )

        self.shell = self.client.invoke_shell()

        time.sleep(2)

        if self.shell.recv_ready():
            self.shell.recv(65535)

        print("[+] Connected to Cowrie")

    def execute(self, command):

        print(f">>> {command}")

        self.shell.send(command + "\n")

        time.sleep(2)

        output = ""

        while self.shell.recv_ready():
            output += self.shell.recv(65535).decode(
                errors="ignore"
            )

        return output

    def close(self):

        if self.shell:
            self.shell.send("exit\n")

        time.sleep(1)

        if self.client:
            self.client.close()

        print("[+] SSH connection closed")