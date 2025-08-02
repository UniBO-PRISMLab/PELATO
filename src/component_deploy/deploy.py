import docker
import os
import logging
import yaml
import time
from ..colors import Colors

def deploy_components(project_dir, nats_host, nats_port, detached, metrics, metrics_enabled):

    deploy_metrics = {}
    
    # Check if the project directory is valid
    if not os.path.exists(f"{project_dir}/gen"):
        logging.error(f"{Colors.RED}Project directory is not valid{Colors.RESET}")
        return
    
    print(f'{Colors.BLUE}Deploying WASM components{Colors.RESET}')
    
    # Docker client
    client = docker.from_env()
    
    if metrics_enabled:
        start_time = time.time()
    
    # Build the images for the project if they don't exist
    try:
        client.images.get("wash-deploy-image:latest")
    except:
        
        print(f'{Colors.YELLOW} - Building wash-deploy-image from Dockerfile...{Colors.RESET}')
        client.images.build(
            path="src/component_deploy/docker",
            dockerfile="deploy.Dockerfile",
            tag="wash-deploy-image:latest"
        )
        if metrics_enabled:
            deploy_metrics['image_build_time'] = '%.3f'%(time.time() - start_time)
        
    try:
        wait_list = []
        
        for task in os.listdir(f"{project_dir}/gen"):
            __deploy_wadm(f"{project_dir}/gen/{task}", client, nats_host, nats_port, detached, wait_list)
            
        if detached == 'True':
            
            print(f'{Colors.BLUE}Waiting for deployment...{Colors.RESET}')
            for container_name in wait_list:
                try:
                    container = client.containers.get(container_name)
                    result = container.wait()
                    exit_code = result['StatusCode']
                    
                    if exit_code == 0:
                        print(f"{Colors.GREEN} - Deployment successful for {container_name}, removing container{Colors.RESET}")
                        container.remove()
                    else:
                        print(f"{Colors.RED} - Deployment failed for {container_name} (exit code: {exit_code}), keeping container for debugging{Colors.RESET}")
                        
                except Exception as e:
                    print(f"{Colors.YELLOW} - Error waiting for container {container_name}: {e}{Colors.RESET}")
                    continue
        
    except Exception as e:
        logging.error(f"{Colors.RED}Error deploying project: {e}{Colors.RESET}")
        return
    
    if metrics_enabled:
        deploy_metrics['components_deploy_time'] = '%.3f'%(time.time() - start_time)
        metrics['deploy'] = deploy_metrics
        
    print(f"{Colors.GREEN}Project deployed successfully{Colors.RESET}")
    
def __deploy_wadm(task_dir, client, nats_host, nats_port, detached, wait_list):
    
    wadm = __parse_yaml(f"{task_dir}/wadm.yaml")
    
    path = os.path.abspath(task_dir)
    
    name = wadm['spec']['components'][0]['name'] + '-deploy'
    
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
    print(f"{Colors.BLUE} - Deploying WASM module {name}{Colors.RESET}")
    container = client.containers.run(
        "wash-deploy-image:latest",
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