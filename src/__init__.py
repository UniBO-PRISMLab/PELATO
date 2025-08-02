import os
from dotenv import load_dotenv
import src.code_generator.generator as code_generator
import src.wasm_builder.build as wasm_builder
import src.component_deploy.deploy as deployer
import src.component_deploy.remove as remover
import time
from .colors import Colors

class Pelato:
    def __init__(self):
        
        self.setup_vars()
        
    def setup_vars(self):
        
        load_dotenv(override=True)
        
        self.registry_url = os.getenv('REGISTRY_URL')
        self.reg_user = os.getenv('REGISTRY_USER')
        self.reg_pass = os.getenv('REGISTRY_PASSWORD')
        self.detached = os.getenv('PARALLEL_BUILD')
        self.nats_host = os.getenv('NATS_HOST')
        self.nats_port = os.getenv('NATS_PORT')
        self.metrics_enabled = os.getenv('ENABLE_METRICS') == 'True'
        self.metrics = {}
        
    def generate(self, project_dir):
        code_generator.generate(project_dir, self.registry_url, self.metrics, self.metrics_enabled)
        
    def build(self, project_dir):
        wasm_builder.build_project(project_dir, self.reg_user, self.reg_pass, self.detached, self.metrics, self.metrics_enabled)
        
    def deploy(self, project_dir):
        deployer.deploy_components(project_dir, self.nats_host, self.nats_port, self.detached, self.metrics, self.metrics_enabled)
        
    def remove(self, project_dir):
        self.metrics_enabled = False
        remover.remove_components(project_dir, self.nats_host, self.nats_port, self.detached)

    def all(self, project_dir):
        
        print(f'{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.RESET}')
        print(f"{Colors.MAGENTA}🚀 Starting PELATO full pipeline for project {project_dir}{Colors.RESET}")
        print(f'{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.RESET}')
        
        print(f"\n{Colors.BLUE}📋 Step 1/3: Code Generation{Colors.RESET}")
        self.generate(project_dir)
        time.sleep(1)
        
        print(f"\n{Colors.BLUE}🔨 Step 2/3: Building Components{Colors.RESET}")
        self.build(project_dir)
        time.sleep(1)
        
        print(f"\n{Colors.BLUE}🚀 Step 3/3: Deploying Components{Colors.RESET}")
        self.deploy(project_dir)
        
        print(f"\n{Colors.GREEN}🎉 PELATO pipeline completed successfully!{Colors.RESET}")
        print(f'{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.RESET}')