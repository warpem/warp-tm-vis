from enum import Enum
from pathlib import Path

import mrcfile
import napari
import napari.utils.notifications
import rich
import typer
from magicgui import magicgui

from .utils import (
    find_correlation_volume_file,
    update_volume_layers,
    update_particle_layer,
    get_particle_positions_and_cc
)

console = rich.console.Console()

cli = typer.Typer(add_completion=False)


@cli.command(
    no_args_is_help=True,
    help="Visualize Warp template matching results and the effects of thresholding"
)
def warp_tm_vis(
    reconstruction_directory: Path = typer.Option(
        ...,
        '--reconstruction-directory', '-rdir',
        help="directory containing tomograms e.g. warp_tiltseries/reconstruction/deconv"
    ),
    matching_directory: Path = typer.Option(
        ...,
        '--matching-directory', '-mdir',
        help="matching directory e.g. warp_tiltseries/matching"
    ),
    matching_pattern: str = typer.Option(
        ...,
        '--matching-pattern', '-mp',
        help="matching pattern e.g. \"*_flipx.star\""
    ),
    correlation_volume_pattern: str = typer.Option(
        ...,
        '--correlation-volume-pattern', '-cvp',
        help="correlation volume pattern e.g. \"*_flipx_corr.mrc\""
    ),
    load_volumes: bool = typer.Option(
        default=True,
        help="whether or not to load reconstructions and correlation volumes"
    ),
):
    # grab files
    particle_files = list(matching_directory.glob(matching_pattern))
    tomogram_files = list(reconstruction_directory.glob('*.mrc'))
    correlation_volume_files = list(matching_directory.glob(correlation_volume_pattern))

    console.log(f"found {len(particle_files)} particle files")
    console.log(f"found {len(tomogram_files)} tomogram files")
    console.log(f"found {len(correlation_volume_files)} correlation volume files")

    with console.status("launching napari viewer...", spinner="arc"):
        viewer = napari.Viewer(ndisplay=3)
    console.log("napari viewer launched")

    viewer.title = "warp-tm-vis"

    tomogram_files = [str(path) for path in tomogram_files]
    Tomogram = Enum('Tomogram', ' '.join(tomogram_files))

    @magicgui(auto_call=True)
    def add_tomogram(tomogram: Tomogram):
        # load volumes
        if load_volumes is True:
            console.log(f"loading tomogram from {tomogram}...")
            volume = mrcfile.read(tomogram.name)
            console.log(f"tomogram loaded")

            correlation_volume_file = find_correlation_volume_file(
                tomogram_file=Path(tomogram.name),
                correlation_volume_files=correlation_volume_files
            )
            console.log(f"loading correlation volume from {correlation_volume_file}")
            correlation_volume = mrcfile.read(correlation_volume_file)
            console.log(f"correlation volume loaded")

        # load particle positions and cc values
        console.log(f"loading particle metadata...")
        zyx, cc = get_particle_positions_and_cc(tomogram.name, particle_files=particle_files)
        console.log(f"particle metadata loaded")

        # notify user of max cc
        ts_id = Path(tomogram.name).name
        napari.utils.notifications.show_info(f"max cc for {ts_id} is {cc.max()}")

        # Update volumes in viewer
        if load_volumes is True:
            update_volume_layers(viewer, volume, correlation_volume, load_volumes=True)

        # Update particles
        update_particle_layer(viewer, zyx, cc, tomogram.name)

    # create interactive widget for subsetting particles
    @magicgui(auto_call=True)
    def subset_particles(min_cc: float = 0.0):
        cc = viewer.layers['particles'].metadata['cc']
        zyx = viewer.layers['particles'].metadata['positions']
        zyx = zyx[cc >= min_cc]
        viewer.layers['particles'].data = zyx

    # add widgets for changing tomogram and subsetting particles to viewer
    viewer.window.add_dock_widget(add_tomogram, area='bottom')
    viewer.window.add_dock_widget(subset_particles, area='bottom')

    # initialise widget and launch viewer
    add_tomogram()
    napari.run()
