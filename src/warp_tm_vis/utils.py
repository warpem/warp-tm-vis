from pathlib import Path

import mrcfile
import napari
import numpy as np
import starfile


def update_volume_layers(
    viewer: napari.Viewer,
    volume: np.ndarray,
    correlation_volume: np.ndarray,
    load_volumes=True
):
    if not load_volumes:
        return

    if 'tomogram' not in viewer.layers:
        viewer.add_image(data=volume, name='tomogram', colormap='gray_r')
    else:
        viewer.layers['tomogram'].data = volume

    if 'correlation_volume' not in viewer.layers:
        viewer.add_image(
            data=correlation_volume,
            name='correlation_volume',
            colormap='inferno',
            contrast_limits=[2, 10],
            blending='additive'
        )
    else:
        viewer.layers['correlation_volume'].data = correlation_volume


def update_particle_layer(
    viewer: napari.Viewer,
    zyx: np.ndarray,
    cc: np.ndarray,
    tomogram_name: str
):
    if 'particles' not in viewer.layers:
        viewer.add_points(
            zyx,
            name='particles',
            size=6,
            metadata={
                'positions': zyx,
                'cc': cc,
                'ts_id': tomogram_name
            },
            face_color='orange',
            opacity=0.75,
            out_of_slice_display=True,
        )
    else:
        viewer.layers['particles'].data = zyx
        viewer.layers['particles'].metadata['positions'] = zyx
        viewer.layers['particles'].metadata['cc'] = cc
        viewer.layers['particles'].metadata['ts_id'] = tomogram_name


def get_particle_positions_and_cc(tomogram_file: str, particle_files: list[Path]) -> np.ndarray:
    df = starfile.read(find_particles_file(Path(tomogram_file), particle_files=particle_files))
    zyx = df[['rlnCoordinateZ', 'rlnCoordinateY', 'rlnCoordinateX']].to_numpy()
    cc = df['rlnAutopickFigureOfMerit'].to_numpy()
    with mrcfile.open(tomogram_file, header_only=True) as mrc:
        nz, ny, nx = mrc.header.nz, mrc.header.ny, mrc.header.nx
    return zyx * np.array([nz, ny, nx]), cc


def find_particles_file(tomogram_file: Path, particle_files: list[Path]) -> Path | None:
    matching_files = [
        f for f in particle_files
        if f.name.startswith(tomogram_file.stem)
    ]
    if len(matching_files) == 1:
        return matching_files[0]
    else:
        raise RuntimeError('found no files or too many files')


def find_correlation_volume_file(tomogram_file: Path, correlation_volume_files: list[Path]) -> Path | None:
    matching_files = [
        f for f in correlation_volume_files
        if f.name.startswith(tomogram_file.stem)
    ]
    if len(matching_files) == 1:
        return matching_files[0]
    else:
        raise RuntimeError('found no files or too many files')
