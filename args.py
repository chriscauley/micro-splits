import typer

video_path = typer.Argument(None, help="path to mkv file of metroid game")
add_items = typer.Option(False, help="will prompt the user to add new items")