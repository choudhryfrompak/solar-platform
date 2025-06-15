# backend/template_manager.py
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class TemplateManager:
    def __init__(self, templates_dir: str = "/app/templates"):
        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    def get_template_types(self) -> list:
        """Get list of available template types"""
        return [d.name for d in self.templates_dir.iterdir() if d.is_dir()]

    def validate_config(self, template_type: str, config: Dict[str, Any]) -> bool:
        """Validate configuration against template requirements"""
        required_fields = {
            "goodwe": {
                "sems": ["username", "password", "region"],
                "influxdb": ["url", "token", "org", "bucket"],
                "settings": ["interval", "timezone"]
            }
        }

        if template_type not in required_fields:
            logger.error(f"Unknown template type: {template_type}")
            return False

        for section, fields in required_fields[template_type].items():
            if section not in config:
                logger.error(f"Missing section in config: {section}")
                return False
            for field in fields:
                if field not in config[section]:
                    logger.error(f"Missing field in config: {section}.{field}")
                    return False
                if not config[section][field] and field not in ["password"]:
                    logger.error(f"Empty field in config: {section}.{field}")
                    return False

        return True

    def create_container(self, template_type: str, container_name: str, config: Dict[str, Any]) -> Optional[str]:
        """Create a new container from template"""
        try:
            # Validate inputs
            if not template_type or not container_name:
                raise ValueError("Template type and container name are required")

            template_dir = self.templates_dir / template_type
            if not template_dir.exists():
                raise FileNotFoundError(f"Template not found: {template_type}")

            # Validate configuration
            if not self.validate_config(template_type, config):
                raise ValueError("Invalid configuration")

            # Create container directory
            container_dir = Path("/app/containers") / container_name
            if container_dir.exists():
                raise FileExistsError(f"Container already exists: {container_name}")

            # Copy template files
            shutil.copytree(template_dir, container_dir)

            # Write configuration
            config_file = container_dir / "config.json"
            with config_file.open('w') as f:
                json.dump(config, f, indent=2)

            # Make scraper executable
            scraper_file = container_dir / "scraper.py"
            if scraper_file.exists():
                scraper_file.chmod(0o755)

            logger.info(f"Container created successfully: {container_name}")
            return str(container_dir)

        except Exception as e:
            logger.error(f"Failed to create container: {str(e)}")
            # Clean up on failure
            if 'container_dir' in locals() and container_dir.exists():
                shutil.rmtree(container_dir)
            return None

    def remove_container(self, container_name: str) -> bool:
        """Remove a container"""
        try:
            container_dir = Path("/app/containers") / container_name
            if not container_dir.exists():
                logger.warning(f"Container not found: {container_name}")
                return False

            shutil.rmtree(container_dir)
            logger.info(f"Container removed successfully: {container_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove container: {str(e)}")
            return False

    def list_containers(self) -> list:
        """List all containers"""
        containers_dir = Path("/app/containers")
        if not containers_dir.exists():
            return []
        return [d.name for d in containers_dir.iterdir() if d.is_dir()]

    def load_template(self, template_name: str) -> Optional[Dict]:
        """Load template configuration"""
        template_path = self.templates_dir / template_name / "template.json"
        if not template_path.exists():
            return None
            
        try:
            with open(template_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def list_templates(self) -> List[str]:
        """List available templates"""
        templates = []
        for template_dir in self.templates_dir.iterdir():
            if template_dir.is_dir() and (template_dir / "template.json").exists():
                templates.append(template_dir.name)
        return templates
    
    def copy_template_files(self, template_name: str, destination: Path) -> bool:
        """Copy template files to destination"""
        template = self.load_template(template_name)
        if not template:
            return False
            
        source_dir = self.templates_dir / template_name
        destination.mkdir(exist_ok=True)
        
        try:
            for template_file, actual_file in template["files"].items():
                source_file = source_dir / actual_file
                dest_file = destination / template_file
                if source_file.exists():
                    shutil.copy2(source_file, dest_file)
            return True
        except Exception:
            return False
    
    def validate_template(self, template_name: str) -> bool:
        """Validate template has required files"""
        template = self.load_template(template_name)
        if not template:
            return False
            
        source_dir = self.templates_dir / template_name
        required_files = template.get("files", {}).values()
        
        return all((source_dir / file).exists() for file in required_files)