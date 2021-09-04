## Environment Setup
All the code have been run and tested on Ubuntu 16.04, Python 2.7 (and 3.8), Pytorch 1.1.0 (and 1.2.0), CUDA 10.0, TITAN X/Xp and GTX 1080Ti GPUs

- Go into the downloaded code directory
```bash
cd <path_to_downloaded_directory>
```
- Setup python environment
```bash
conda create --name defgrid
conda activate defgrid
conda install pytorch==1.2.0 torchvision==0.4.0 cudatoolkit=10.0 -c pytorch
pip install opencv-python matplotlib networkx tensorboardx tqdm scikit-image ipdb
```
- Add the project to PYTHONPATH  
```bash
export PYTHONPATH=$PWD:$PYTHONPATH
```

### Train DefGrid on Cityscapes Images

#### Data 
- Download the Cityscapes dataset (leftImg8bit\_trainvaltest.zip) from the official [website](https://www.cityscapes-dataset.com/downloads/) [11 GB]
- Our dataloaders work with our processed annotation files which can be downloaded from [here](http://www.cs.toronto.edu/~amlan/data/polygon/cityscapes.tar.gz).
- From the root directory, run the following command with appropriate paths to get the annotation files ready for your machine
```bash
python scripts/dataloaders/change_paths.py --city_dir <path_to_downloaded_leftImg8bit_folder> --json_dir <path_to_downloaded_annotation_file> --out_dir <output_dir>
```

#### Training

Train DefGrid on the whole traininig set.
```bash
python scripts/train/train_def_grid_full.py --debug false --version train_on_cityscapes_full --encoder_backbone simplenn --resolution 512 1024 --grid_size 20 40 --w_area 0.005
```

