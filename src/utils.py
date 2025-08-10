import yaml
import os
from .colors import Colors

def dump_metrics(metrics, project_dir):
    
    with open(f"{project_dir}/metrics.yaml", 'w') as file:
        yaml.dump(metrics, file)
    
    print(f"{Colors.BLUE}📊 Metrics saved in {project_dir}/metrics.yaml{Colors.RESET}")
    
    return

def load_metrics(project_dir):
    
    if not os.path.exists(f"{project_dir}/metrics.yaml"):
        return {
            "runs": []
        }
    
    with open(f"{project_dir}/metrics.yaml", 'r') as file:
        metrics = yaml.safe_load(file)
    
    return metrics

def get_available_templates():

    ## Read all directories found inside code_generator/templates and return the names as a list
    templates_dir = "src/code_generator/templates"
    return [name for name in os.listdir(templates_dir) if os.path.isdir(os.path.join(templates_dir, name))]