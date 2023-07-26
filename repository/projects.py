

from typing import Optional

from rich.console import Console
from rich.table import Table

from data.database import read_only_session, read_write_session
from data.projects import Project
from index.embeddings import create_embeddings_for_chunks
from index.file_processor import chunk_source_files, source_files
from repository.indexes import complete_indexing, start_indexing

console = Console()


def get_project_by_name(name: str) -> Optional[Project]:
    """Get project by name if it exists.

    Args:
        name (str): name of the project

    Returns:
        Project: project object
    """
    with read_only_session() as session:
        project = session.query(Project).filter_by(name=name).first()
        if project:
            return project
        else:
            console.print(f"Project with name - {name} does not exist.")
            return None


def list_all_projects():
    """List all projects created."""
    with read_only_session() as session:
        projects = session.query(Project).all()
        table = Table(title="Projects")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Path", style="green", no_wrap=True)
        table.add_column("Created at", style="red", no_wrap=True)

        datetime_format = "%B %d, %Y, %I:%M %p"

        for project in projects:
            table.add_row(
                project.name,
                project.path,
                project.created_at.strftime(datetime_format),
            )

        console.print(table)

def create_or_update_project(name: str, path: str):
    """ Check if project already exists with this path.

    - If it does, start indexing it.
    - If it doesn't, create it and start indexing it.

    Args:
        name (str): name of the project
        path (str): unique path to the project
    """
    with read_write_session() as session:
        project = session.query(Project).filter_by(path=path).first()
        if project and project.name == name:
            console.print(f"Project already exists at {path}.")
        elif project and project.name != name:
            console.print(f"Updating project name from {project.name} to {name}")
            project.name = name
        elif project and project.path != path:
            console.print(f"Updating project path from {project.path} to {path}")
            project.path = path
        else:
            console.print(f"Creating new project - {name} at {path}")
            project = Project(name=name, path=path)
            session.add(project)

        session.commit()
        session.refresh(project)
        if project:
            index_project(project)

def index_project(project: Project):
    """ Start indexing the project.

    Args:
        project (Projects): project to index
    """
    console.print(f"Indexing - {project.name} at {project.path}")
    index_id = start_indexing(project)
    chunk_result = chunk_source_files(source_files(project))
    create_embeddings_for_chunks(project.id, index_id, chunk_result.chunks)
    complete_indexing(index_id, chunk_result.indexed, chunk_result.skipped)