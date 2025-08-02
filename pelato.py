import argparse
import src
import src.utils as ut
import time
import sys
from src.colors import Colors

def print_banner():
    banner = f"""
{Colors.CYAN}
╔═══════════════════════════════════════════════════════════════╗
║                            PELATO                             ║
║              WebAssembly Component Builder & Deployer        ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.RESET}
"""
    print(banner)

def validate_directory(directory):
    """Validate if the provided directory exists and contains required files"""
    import os
    
    if not os.path.exists(directory):
        print(f"{Colors.RED}❌ Error: Directory '{directory}' does not exist{Colors.RESET}")
        return False
    
    # Check for workflow.yaml for commands that need it
    workflow_file = os.path.join(directory, "workflow.yaml")
    if not os.path.exists(workflow_file):
        print(f"{Colors.YELLOW}⚠️  Warning: 'workflow.yaml' not found in '{directory}'{Colors.RESET}")
        print(f"{Colors.YELLOW}   This might cause issues with generation and building{Colors.RESET}")
        
    return True

def suggest_command(invalid_command):
    """Suggest similar commands when user types invalid command"""
    commands = ["gen", "build", "deploy", "remove", "brush"]
    suggestions = []
    
    for cmd in commands:
        # Simple similarity check
        if invalid_command.lower() in cmd or cmd in invalid_command.lower():
            suggestions.append(cmd)
        elif len(invalid_command) > 2 and any(c in cmd for c in invalid_command):
            suggestions.append(cmd)
    
    if suggestions:
        print(f"{Colors.YELLOW}💡 Did you mean one of these commands?{Colors.RESET}")
        for suggestion in suggestions[:3]:  # Show max 3 suggestions
            print(f"   {Colors.CYAN}• {suggestion}{Colors.RESET}")
    
    print(f"\n{Colors.BLUE}Available commands:{Colors.RESET}")
    print(f"   {Colors.GREEN}gen{Colors.RESET}     - Generate Go code from workflow")
    print(f"   {Colors.GREEN}build{Colors.RESET}   - Build WASM components")
    print(f"   {Colors.GREEN}deploy{Colors.RESET}  - Deploy WASM components")
    print(f"   {Colors.GREEN}remove{Colors.RESET}  - Remove deployed WASM components")
    print(f"   {Colors.GREEN}brush{Colors.RESET}   - Full pipeline: gen → build → deploy")

def main():
    
    print_banner()
    
    # Custom help formatter to control output
    class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
        def add_usage(self, usage, actions, groups, prefix=None):
            # Skip adding usage line
            pass
            
        def format_help(self):
            # Custom help format without "positional arguments" section
            help_text = f"""
{Colors.BLUE}Generate, build and deploy WASM components written in Go{Colors.RESET}

{Colors.CYAN}Available Commands:{Colors.RESET}
  {Colors.GREEN}gen{Colors.RESET}     Generate Go code from workflow configuration
  {Colors.GREEN}build{Colors.RESET}   Build WASM components from generated code  
  {Colors.GREEN}deploy{Colors.RESET}  Deploy WASM components to wasmCloud
  {Colors.GREEN}remove{Colors.RESET}  Remove deployed WASM components
  {Colors.GREEN}brush{Colors.RESET}   Run complete pipeline: generate → build → deploy

{Colors.CYAN}Usage:{Colors.RESET}
  {Colors.YELLOW}python3 pelato.py <command> <project_directory>{Colors.RESET}

{Colors.CYAN}Examples:{Colors.RESET}
  {Colors.GREEN}python3 pelato.py gen project/{Colors.RESET}        Generate code for project
  {Colors.GREEN}python3 pelato.py build project/{Colors.RESET}      Build WASM components  
  {Colors.GREEN}python3 pelato.py deploy project/{Colors.RESET}     Deploy components
  {Colors.GREEN}python3 pelato.py brush project/{Colors.RESET}      Run full pipeline

{Colors.CYAN}Environment Variables:{Colors.RESET}
  REGISTRY_URL, REGISTRY_USER, REGISTRY_PASSWORD
  NATS_HOST, NATS_PORT, PARALLEL_BUILD, ENABLE_METRICS
"""
            return help_text
    
    parser = argparse.ArgumentParser(
        formatter_class=ColoredHelpFormatter,
        add_help=False  # Disable default help to use our custom one
    )
    # Add custom help option
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')
    
    subparsers = parser.add_subparsers(dest="command")

    # Generate command
    parser_generate = subparsers.add_parser("gen", add_help=False)
    parser_generate.add_argument("dir", type=str, nargs='?')

    # Build command  
    parser_build = subparsers.add_parser("build", add_help=False)
    parser_build.add_argument("dir", type=str, nargs='?')

    # Deploy command
    parser_deploy = subparsers.add_parser("deploy", add_help=False)
    parser_deploy.add_argument("dir", type=str, nargs='?')
    
    # Remove command
    parser_remove = subparsers.add_parser("remove", add_help=False)
    parser_remove.add_argument("dir", type=str, nargs='?')
    
    # Full pipeline command
    parser_all = subparsers.add_parser("brush", add_help=False)
    parser_all.add_argument("dir", type=str, nargs='?')

    # Parsing degli argomenti
    args = parser.parse_args()
    
    # Check if help was requested
    if hasattr(args, 'help') and args.help:
        parser.print_help()
        sys.exit(0)
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        print(f"\n{Colors.RED}❌ Error: No command specified{Colors.RESET}")
        #suggest_command("")
        sys.exit(1)
    
    # Check if directory was provided
    if not args.dir:
        parser.print_help()
        print(f"\n{Colors.RED}❌ Error: Project directory is required{Colors.RESET}")
        sys.exit(1)
    
    # Validate directory
    if not validate_directory(args.dir):
        sys.exit(1)
    
    # Setup Pelato
    print(f"{Colors.BLUE}🔧 Initializing PELATO...{Colors.RESET}")
    pelato = src.Pelato()
    
    if pelato.metrics_enabled:
        print(f"{Colors.CYAN}📊 Metrics collection enabled{Colors.RESET}")
        pelato.metrics = {}
        start_time = time.time()

    # Esecuzione del comando specificato
    print(f"{Colors.MAGENTA}🚀 Executing command: {args.command}{Colors.RESET}")
    print(f"{Colors.BLUE}📁 Project directory: {args.dir}{Colors.RESET}\n")
    
    try:
        if args.command == "gen":
            pelato.generate(args.dir)
        elif args.command == "build":
            pelato.build(args.dir)
        elif args.command == "deploy":
            pelato.deploy(args.dir)
        elif args.command == "remove":
            pelato.remove(args.dir)
        elif args.command == "brush":
            pelato.all(args.dir)
        else:
            print(f"{Colors.RED}❌ Unknown command: '{args.command}'{Colors.RESET}")
            suggest_command(args.command)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Operation cancelled by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Unexpected error: {e}{Colors.RESET}")
        sys.exit(1)

    if pelato.metrics_enabled:
        end_time = time.time()
        pelato.metrics['time_total'] = '%.3f'%(end_time - start_time)
        
        print(f"\n{Colors.CYAN}📊 Saving metrics...{Colors.RESET}")
        full_metrics = ut.load_metrics(args.dir)
        full_metrics['runs'].append(pelato.metrics)
        ut.dump_metrics(full_metrics, args.dir)
        print(f"{Colors.GREEN}✅ Metrics saved successfully{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}🎉 PELATO execution completed successfully!{Colors.RESET}")
        
if __name__ == "__main__":
    main()
