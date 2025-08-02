import yaml
import shutil
import logging
import os
import src.code_generator.template_compiler as template_compiler
import time
from ..colors import Colors

def __parse_yaml(yaml_file):
    with open(yaml_file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None
        
def __remove_dir_if_exists(dir_path):
    
    if os.path.exists(dir_path):
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path)

def generate(project_dir, registry_url, metrics, metrics_enabled):
    
    gen_metrics = {}
    start_time = 0
    
    # Check if the project directory is valid
    if not os.path.exists(f"{project_dir}/workflow.yaml") or not os.path.exists(f"{project_dir}/tasks"):
        logging.error(f"{Colors.RED}Project directory is not valid{Colors.RESET}")
        return
    
    # Parsing del file di configurazione
    config = __parse_yaml(f"{project_dir}/workflow.yaml")
    
    if config is None:
        logging.error(f"{Colors.RED}Error parsing workflow.yaml{Colors.RESET}")
        return
    
    print(f"{Colors.BLUE}Generating code for project {config['project_name']}{Colors.RESET}")
    
    if metrics_enabled:
        metrics['n_task'] = len(config['tasks'])
        start_time = time.time()
    
    # Rimozione della cartella di output
    output_dir = f"{project_dir}/gen"
    __remove_dir_if_exists(output_dir)
    
    # Creazione della cartella di output
    os.makedirs(output_dir, exist_ok=True)
    
    # for each task in the workflow
    for task in config['tasks']:
        
        try:
            task['registry_url'] = registry_url
            template_compiler.handle_task(task, output_dir)

            # Copy the code file to the output folder
            shutil.copy2(f"{project_dir}/tasks/{task['code']}", f"{output_dir}/{task['component_name']}/{task['code']}")
            
            print(f"{Colors.GREEN} - Task {task['component_name']} generated{Colors.RESET}")
            
        except Exception as e:
            logging.error(f"{Colors.RED}Error generating task {task['component_name']}: {e}{Colors.RESET}")
            continue
        
    if metrics_enabled:
        end_time = time.time()
        gen_metrics['gen_time'] = '%.3f'%(end_time - start_time)
        metrics['code_gen'] = gen_metrics
        
    print(f"{Colors.GREEN}Code generation completed{Colors.RESET}")