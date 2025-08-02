import docker
import os
import logging
import yaml
from ..colors import Colors

def remove_components(project_dir, nats_host, nats_port, detached):

    # Check if the project directory is valid
    if not os.path.exists(f"{project_dir}/gen"):
        logging.error(f"{Colors.RED}Project directory is not valid{Colors.RESET}")
        return
    
    print(f'{Colors.BLUE}Removing WASM components{Colors.RESET}')
    
    # Docker client
    client = docker.from_env()
    
    # Build the images for the project if they don't exist
    try:
        client.images.get("wash-remove-image:latest")
    except docker.errors.ImageNotFound:
        
        print(f'{Colors.YELLOW} - Building wash-remove-image from Dockerfile...{Colors.RESET}')
        client.images.build(
            path="src/component_deploy/docker",
            dockerfile="remove.Dockerfile",
            tag="wash-remove-image:latest"
        )
        
    try:
        wait_list = []
        
        for task in os.listdir(f"{project_dir}/gen"):
            __remove_wadm(f"{project_dir}/gen/{task}", client, nats_host, nats_port, detached, wait_list)
            
        if detached == 'True':
            
            print(f'{Colors.BLUE}Waiting for component remove...{Colors.RESET}')
            for container_name in wait_list:
                try:
                    container = client.containers.get(container_name)
                    result = container.wait()
                    exit_code = result['StatusCode']
                    
                    if exit_code == 0:
                        print(f"{Colors.GREEN} - Remove successful for {container_name}, removing container{Colors.RESET}")
                        container.remove()
                    else:
                        print(f"{Colors.RED} - Remove failed for {container_name} (exit code: {exit_code}), keeping container for debugging{Colors.RESET}")
                        
                except Exception as e:
                    print(f"{Colors.YELLOW} - Error waiting for container {container_name}: {e}{Colors.RESET}")
                    continue
        
    except Exception as e:
        logging.error(f"{Colors.RED}Error removing components: {e}{Colors.RESET}")
        return
    
    print(f"{Colors.GREEN}Components removed successfully{Colors.RESET}")
    
    
def __remove_wadm(task_dir, client, nats_host, nats_port, detached, wait_list):
    
    wadm = __parse_yaml(f"{task_dir}/wadm.yaml")
    
    path = os.path.abspath(task_dir)
    
    name = wadm['spec']['components'][0]['name'] + '-remove'
    
    # Check if container with the same name already exists and remove it
    try:
        existing_container = client.containers.get(name)
        print(f"{Colors.YELLOW} - Removing existing container {name}{Colors.RESET}")
        existing_container.remove(force=True)
    except docker.errors.NotFound:
        # Container doesn't exist, continue
        pass
    except Exception as e:
        print(f"{Colors.RED} - Warning: Could not remove existing container {name}: {e}{Colors.RESET}")
    
    # Build the wasm module
    print(f"{Colors.BLUE} - Removing WASM module {name} from WasmCloud{Colors.RESET}")
    container = client.containers.run(
        "wash-remove-image:latest",
        environment=[f'WASMCLOUD_CTL_HOST={nats_host}',
                     f'WASMCLOUD_CTL_PORT={nats_port}'],
        volumes={path: {'bind': '/app', 'mode': 'rw'}},
        remove=False,
        detach=True,
        name=name
    )
    
    if detached == 'False':
        container.wait()
    else:
        wait_list.append(name)
    

def __parse_yaml(yaml_file):
    with open(yaml_file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None