# qet/exceptions.py

class QetError(Exception):
    """Base exception for all qet errors."""
    pass

class ConfigError(QetError):
    """Raised when there is an error loading or parsing configuration files."""
    pass

class PackageNotFoundError(QetError):
    """Raised when a package cannot be found in the definitions database."""
    pass

class MethodNotAvailableError(QetError):
    """Raised when an installation method is not available for a package or on the system."""
    pass

class ExecutionError(QetError):
    """Raised when a shell command fails to execute successfully."""
    def __init__(self, message, command=None, returncode=None, stdout=None, stderr=None):
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

class AllMethodsFailedError(QetError):
    """Raised when every candidate method for a package has been tried and failed."""
    def __init__(self, qet_name: str, failures: list):
        # failures: list of (method_name, returncode, stderr) tuples
        super().__init__(f"All installation methods failed for '{qet_name}'.")
        self.qet_name = qet_name
        self.failures = failures  # [(method, returncode, stderr), ...]
