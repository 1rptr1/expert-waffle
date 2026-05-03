import shutil
import subprocess
import requests
import time
import platform
from typing import Optional, List

class OllamaManager:
    """Manage Ollama installation, service, and models"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.default_models = ["llama3", "mistral"]
    
    def is_ollama_installed(self) -> bool:
        """Check if Ollama is installed"""
        return shutil.which("ollama") is not None
    
    def is_ollama_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def is_model_present(self, model: str) -> bool:
        """Check if a model is already downloaded"""
        if not self.is_ollama_installed():
            return False
            
        try:
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return model in result.stdout
        except:
            return False
    
    def install_ollama_linux(self) -> bool:
        """Install Ollama on Linux systems"""
        if platform.system() != "Linux":
            print("⚠️ Ollama auto-install only supported on Linux")
            return False
        
        try:
            print("📦 Installing Ollama (Linux)...")
            cmd = "curl -fsSL https://ollama.com/install.sh | sh"
            result = subprocess.run(cmd, shell=True, check=True, timeout=300)
            print("✅ Ollama installed successfully")
            return True
        except subprocess.TimeoutExpired:
            print("⚠️ Ollama installation timed out")
            return False
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Ollama installation failed: {e}")
            return False
    
    def start_ollama_service(self) -> bool:
        """Start Ollama as a background service"""
        try:
            print("🚀 Starting Ollama service...")
            process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Give it time to start
            time.sleep(3)
            
            # Verify it's running
            if self.is_ollama_running():
                print("✅ Ollama service started successfully")
                return True
            else:
                print("⚠️ Ollama service failed to start")
                return False
                
        except Exception as e:
            print(f"⚠️ Failed to start Ollama: {e}")
            return False
    
    def pull_model(self, model: str) -> bool:
        """Download a specific model"""
        if not self.is_ollama_installed():
            print("⚠️ Ollama not installed, cannot download model")
            return False
        
        try:
            print(f"📥 Pulling model: {model} (this may take several minutes)...")
            result = subprocess.run(
                ["ollama", "pull", model],
                check=True,
                timeout=600  # 10 minutes timeout
            )
            print(f"✅ Model {model} downloaded successfully")
            return True
        except subprocess.TimeoutExpired:
            print(f"⚠️ Model download timed out for {model}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to download model {model}: {e}")
            return False
    
    def setup_ollama_complete(self, models: Optional[List[str]] = None) -> bool:
        """Complete Ollama setup with models"""
        if models is None:
            models = self.default_models
        
        success = True
        
        # Step 1: Install Ollama if needed
        if not self.is_ollama_installed():
            if not self.install_ollama_linux():
                return False
        
        # Step 2: Start service if not running
        if not self.is_ollama_running():
            if not self.start_ollama_service():
                return False
        
        # Step 3: Download models
        for model in models:
            if not self.is_model_present(model):
                if not self.pull_model(model):
                    success = False
            else:
                print(f"✅ Model {model} already available")
        
        return success
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if not self.is_ollama_installed():
            return []
        
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse the output to get model names
            models = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    models.append(line.strip())
            
            return models
        except:
            return []
    
    def get_system_info(self) -> dict:
        """Get system information for Ollama setup"""
        return {
            "platform": platform.system(),
            "ollama_installed": self.is_ollama_installed(),
            "ollama_running": self.is_ollama_running(),
            "available_models": self.get_available_models(),
            "default_models": self.default_models
        }

# Global manager instance
_manager = None

def get_ollama_manager() -> OllamaManager:
    """Get or create Ollama manager instance"""
    global _manager
    if _manager is None:
        _manager = OllamaManager()
    return _manager

def setup_ollama_auto(models: Optional[List[str]] = None) -> bool:
    """
    Automatic Ollama setup function
    Installs, starts service, and downloads models
    """
    manager = get_ollama_manager()
    return manager.setup_ollama_complete(models)

def check_ollama_status() -> dict:
    """Check current Ollama status"""
    manager = get_ollama_manager()
    return manager.get_system_info()

def ensure_model_available(model: str) -> bool:
    """Ensure a specific model is available"""
    manager = get_ollama_manager()
    
    if not manager.is_model_present(model):
        print(f"📥 Model {model} not found, downloading...")
        return manager.pull_model(model)
    
    print(f"✅ Model {model} is available")
    return True

# Convenience functions for backward compatibility
def is_ollama_installed() -> bool:
    """Check if Ollama is installed"""
    return get_ollama_manager().is_ollama_installed()

def is_ollama_running() -> bool:
    """Check if Ollama server is running"""
    return get_ollama_manager().is_ollama_running()

def is_model_present(model: str) -> bool:
    """Check if a model is already downloaded"""
    return get_ollama_manager().is_model_present(model)
