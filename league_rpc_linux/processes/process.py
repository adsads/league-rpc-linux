import glob
import os
import sys
import time

import psutil
import pypresence

from league_rpc_linux.colors import Colors


def processes_exists(process_names: list[str]) -> bool:
    """
    Given an array of process names.
    Give a boolean return value if any of the names was a running process in the machine.
    """
    return any(process_exists(process_name) for process_name in process_names)


def process_exists(process_name: str) -> bool:
    """
    Checks if the given process name is running or not.
    """
    for proc in psutil.process_iter():
        try:
            if process_name.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def check_league_client_process():
    """
    Checks league client processes.
    """
    print(Colors.yellow + "Checking if LeagueClient.exe is running...")
    time.sleep(1)

    league_processes = ["LeagueClient.exe", "LeagueClientUx.exe"]

    if processes_exists(process_names=league_processes):
        print(
            Colors.green
            + "League client is running!"
            + Colors.dgray
            + "(3/3)"
            + Colors.reset
        )
    else:
        print(Colors.red + "League client is not running!" + Colors.reset)
        time.sleep(1)
        sys.exit()


def check_riot_games_service_process() -> None:
    """
    Checks that the Riot Games launcher is running.
    """
    print(Colors.yellow + "Checking if Riot Games Launcher is running...")
    time.sleep(2)
    if process_exists("RiotClientServi"):
        print(
            Colors.green
            + "Riot Games Service is running!"
            + Colors.dgray
            + "(2/3)"
            + Colors.reset
        )
    else:
        print(Colors.red + "Riot Games Service is not running!" + Colors.reset)
        time.sleep(1)
        sys.exit()


def check_discord_process(
    process_names: list[str],
    client_id: str,
) -> pypresence.Presence:
    """
    Checks if discord process is running.
    Connects to Discord Rich Presence if it is found.
    """

    print(Colors.yellow + "Checking if Discord is running...")

    look_for_processes = f"({Colors.green}{', '.join(process_names)}{Colors.blue})"

    time.sleep(1)
    if not processes_exists(process_names=process_names):
        print(Colors.red + "Discord not running!" + Colors.reset)

        print(
            f"{Colors.blue}Could not find any process with the names {look_for_processes} running on your system.{Colors.reset}"
        )
        print(
            f"{Colors.blue}Is your Discord process named something else? Try --add-process <name>{Colors.reset}"
        )
        sys.exit()

    print(f"{Colors.green}Discord is running! {Colors.dgray}(1/3){Colors.reset}")
    try:
        rpc = pypresence.Presence(client_id)
        rpc.connect()

    except Exception as exc:
        print(
            f"{Colors.red}PyPresence encountered some problems, and could not connect to your Discord's RPC{Colors.reset}"
        )
        print(
            f"""{Colors.blue}Reasons for this:
    1. One or more of the processes this script was looking for was found {look_for_processes}
        But Pypresence still was unable to detect a running discord-ipc
    2. You may not have a discord ipc running. Try {Colors.reset}``{Colors.green}ls /run/user/*/ | grep discord-ipc-{Colors.reset}``{Colors.blue} There should only be one result {Colors.reset}``{Colors.green}discord-ipc-0={Colors.reset}``
    {Colors.blue}3. Try restarting Discord. (Make sure the process is stopped before doing that.){Colors.reset}
            """
        )
        # If process names were not found, but ipc exists. Try removing them & restarting
        if len((val := check_discord_ipc())) > 1:
            print(
                f"""
{Colors.red}Detected multiple ipc's running.{Colors.reset}
    You seem to have more than 1 ipc running (which is unusual).
    If you know that discord is running, but pypresence keep failing to connect.
    It might be cause you have multiple ipc's running. try removing the following ipc's and {Colors.green}restart discord.{Colors.reset}
    {Colors.yellow}ipc's: {' , '.join(val)}{Colors.reset}
    run: ``{Colors.green}rm  {' '.join(val)}{Colors.reset}``
    Or you just don't have discord up and running..
            """
            )
        print(
            f"{Colors.red}Raising Exception found by PyPresence, and exiting..{Colors.reset}"
        )

        raise exc
    return rpc


def check_discord_ipc() -> list[str]:
    """
    Checks if there are any discord-ipc's running.
    """
    # Paths to check for Discord IPC sockets
    paths_to_check = ["/tmp", "/run/user/*/"]
    ipc_pattern = "discord-ipc-*"
    list_of_ipcs: list[str] = []
    for path in paths_to_check:
        for ipc_socket in glob.glob(os.path.join(path, ipc_pattern)):
            if os.path.exists(ipc_socket):
                list_of_ipcs.append(ipc_socket)
    return list_of_ipcs


def player_state() -> str | None:
    """
    Returns the player state
    """
    current_state: str | None = None

    if process_exists("RiotClientServi"):
        if process_exists("LeagueClient.exe") or process_exists("LeagueClientUx.exe"):
            if process_exists("League of Legends.exe"):
                current_state = "InGame"
            else:
                current_state = "InLobby"
    return current_state
