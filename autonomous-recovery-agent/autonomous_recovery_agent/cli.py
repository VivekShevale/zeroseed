"""
Command Line Interface for Autonomous Recovery Agent
"""
import click
import sys
import logging
from .agent import AutonomousRecoveryAgent, AgentConfig


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """Autonomous Recovery Agent CLI"""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


@cli.command()
@click.option('--app', required=True, help='Flask app import path (e.g., myapp:app)')
@click.option('--mongodb-url', required=True, help='MongoDB connection URL')
@click.option('--port', default=5000, help='Flask app port')
@click.option('--web-ui-port', default=8081, help='Web UI port')
def monitor(app, mongodb_url, port, web_ui_port):
    """Monitor a Flask app with autonomous recovery"""
    try:
        # Import the Flask app
        module_name, app_name = app.split(':')
        import importlib
        module = importlib.import_module(module_name)
        flask_app = getattr(module, app_name)
        
        # Initialize agent
        config = AgentConfig(
            mongodb_url=mongodb_url,
            enable_web_ui=True,
            web_ui_port=web_ui_port
        )
        
        agent = AutonomousRecoveryAgent(
            flask_app=flask_app,
            mongodb_url=mongodb_url,
            config=config
        )
        
        click.echo(f"🚀 Starting Autonomous Recovery Agent...")
        click.echo(f"📊 Web Dashboard: http://localhost:{web_ui_port}")
        click.echo(f"🩺 Health Endpoint: http://localhost:{port}/health")
        click.echo(f"🔌 Monitoring MongoDB: {mongodb_url}")
        
        agent.start()
        
        # Keep the CLI running
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping agent...")
            agent.stop()
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def status():
    """Check agent status"""
    click.echo("Status command - coming soon!")
    click.echo("For now, check the Web UI at http://localhost:8081")


@cli.command()
@click.option('--component', type=click.Choice(['service', 'database']), 
              required=True, help='Component to recover')
@click.option('--reason', default='Manual trigger', help='Reason for recovery')
def trigger(component, reason):
    """Trigger manual recovery"""
    click.echo(f"Triggering recovery for {component}...")
    click.echo(f"Reason: {reason}")
    click.echo("This feature requires an active agent instance")


@cli.command()
def version():
    """Show version information"""
    from . import __version__
    click.echo(f"Autonomous Recovery Agent v{__version__}")


def main():
    """Main entry point for CLI"""
    cli()


if __name__ == '__main__':
    main()