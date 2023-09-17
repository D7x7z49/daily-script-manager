import re
import json
import argparse
import logging
import shutil
import subprocess
import configparser
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 命令行参数相关常量
ARGS_PROJECT = 'project'
ARGS_PROJECT_NAME_PATTERN = r'^[a-zA-Z0-9-_]+$'
ARGS_PROJECT_URL_PATTERN = r'^(http://|https://|git://)[^\s]+$'
ARGS_PROJECT_HELP = '需要创建的项目名称或项目地址链接'
ARGS_PROJECT_CLEAN_HELP = '清理指定项目'

# 配置文件相关常量
CONFIG_FILE = 'config.ini'
CONFIG_ERROR_MSG = '配置文件解析错误: {}'

CONFIG_CORE = 'core'
CONFIG_CORE_REPOSITORY = 'repository'
CONFIG_CORE_WORKSPACE = 'workspace'

# 错误消息
PROJECT_EXISTS_ERROR_MSG = '项目 {} 已存在'
FILE_NOT_FOUND_ERROR_MSG = '不存在 {}'


def error_exit(msg):
    """
    打印错误消息并退出程序。

    Args:
        msg (str): 错误消息。
    """
    logger.error(msg)
    exit(1)

def print_action(msg):
    """
    输出自定义信息。

    Args:
        msg (str): 自定义信息，可以是操作描述或其他内容。
    """
    logger.error(msg)

def execute_command(command, cwd=None):
    try:
        subprocess.run(command, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f'Command execution failed: {e}')


def read_config() -> configparser.ConfigParser:
    """
    读取配置文件并返回配置对象。

    Returns:
        configparser.ConfigParser: 配置对象。
    """
    # 构建配置文件路径
    config_path = Path(__file__).parent.joinpath(CONFIG_FILE)
    
    # 检查文件是否存在
    if not config_path.exists():
        error_exit(FILE_NOT_FOUND_ERROR_MSG.format(config_path))

    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        return config
    except configparser.Error as e:
        error_exit(CONFIG_ERROR_MSG.format(e))
    

def create_project(name, config: configparser.ConfigParser, is_clone=False):
    """
    创建一个新项目。

    Args:
        name (str): 项目名称。
        config (configparser.ConfigParser): 配置对象。
    """

    if is_clone:
        link = name
        name = link.split('/')[-1].split('.')[0]

    directory_path = Path(config.get(CONFIG_CORE, CONFIG_CORE_REPOSITORY))
    workspace_path = Path(config.get(CONFIG_CORE, CONFIG_CORE_WORKSPACE))

    project_dir = directory_path.joinpath(name)
    workspace_file = workspace_path.joinpath(f'{name}.code-workspace')

    workspace_data = {
        "folders": [
            {
                "path": f'{project_dir}',
                "name": name
            }
        ]
    }

    if not project_dir.exists():
        if not is_clone:
            project_dir.mkdir(parents=True, exist_ok=True)
            execute_command(f'git init {project_dir}')
            project_dir.joinpath('README.md').touch()
            project_dir.joinpath('.gitignore').touch()
        else:
            execute_command(f'git clone {link} {project_dir}')
    else:
        error_exit(PROJECT_EXISTS_ERROR_MSG.format(name))

    with workspace_file.open(mode='w', encoding='utf-8') as f:
        json.dump(workspace_data, f, indent=4)

    print_action(f'add + {project_dir}')
    print_action(f'add + {workspace_file}')


def clean_project(name, config: configparser.ConfigParser):
    """
    清理项目目录。

    Args:
        name (str): 项目名称。
        config (configparser.ConfigParser): 配置对象。
    """

    directory_path = Path(config.get(CONFIG_CORE, CONFIG_CORE_REPOSITORY))
    workspace_path = Path(config.get(CONFIG_CORE, CONFIG_CORE_WORKSPACE))

    project_dir = directory_path.joinpath(name)
    workspace_file = workspace_path.joinpath(f'{name}.code-workspace')

    if not project_dir.exists() and not workspace_file.exists():
        error_exit(FILE_NOT_FOUND_ERROR_MSG.format(name))

    if project_dir.exists():
        try:
            shutil.rmtree(project_dir)
        except OSError as e:
            error_exit(f'NOT clean "{name}": {e}')

    if workspace_file.exists():
        try:
            workspace_file.unlink()  # 删除工作区文件
        except OSError as e:
            error_exit(f'NOT clean "{workspace_file}": {e}')

    print_action(f'clean - {project_dir}')
    print_action(f'clean - {workspace_file}')


def main():
    parser = argparse.ArgumentParser(description='创建适合 VS Code 的开源项目')
    
    # 添加一个位置参数，用于接收项目名称
    parser.add_argument(
        ARGS_PROJECT,
        metavar='Name',
        help=ARGS_PROJECT_HELP,
        type=str
    )

    # 清理选项
    parser.add_argument(
        '-c',
        '--clean',
        action='store_true',
        help=ARGS_PROJECT_CLEAN_HELP
    )
    
    # 获取参数
    args = parser.parse_args()

    # 读取配置文件
    config = read_config()

    args_project = args.__dict__[ARGS_PROJECT]

    if args.__dict__['clean']:
        if re.match(ARGS_PROJECT_NAME_PATTERN, args_project):
            clean_project(args_project, config)
        else:
            error_exit(f'error {args_project}: {ARGS_PROJECT_HELP}')
    else:
        if re.match(ARGS_PROJECT_NAME_PATTERN, args_project):
            # 处理项目名称
            create_project(args_project, config)
        elif re.match(ARGS_PROJECT_URL_PATTERN, args_project):
            # 处理项目链接
            create_project(args_project, config, is_clone=True)
        else:
            error_exit(f'{args_project}: {ARGS_PROJECT_HELP}')
    


if __name__ == "__main__":
    main()

