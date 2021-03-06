<p align="left">
  <img src="/docs/images/logo.jpg" width="500">
</p>


## 1. Installation

### 1.1 Download the **ReSowRS** repository

Navigate to the latest release `(v1.0)` on the RHS of the root project page and download and unzip the source code.


### 1.2 Create an environment with Anaconda

To run the code in the project you need to install the required Python packages into an environment. To do this we will use **Anaconda**, which can be downloaded [here](https://www.anaconda.com/download/).

Open the Anaconda prompt (in Mac and Linux, open a terminal window) and use the `cd` command (change directory) to the directory where you have installed the **ReSowRS** repository.

Create a new environment named `resow` with all the required packages and activate this environment by entering the following commands:

```
>>> conda env create --file env/environment.yml
>>> conda activate resow
```

If your terminal command line prompt now starts with `(resow)` you have succeeded.


## 2. Running the code

### 2.1 Set parameters for your local environment

From the directory containing the **ReSowRS** edit the file **resow_config.ini** and set the parameters as required e.g. set the path to the  local directories for the data and EPSG code for the images downloaded from GEE etc.

### 2.2 Execute the processor

In the terminal window opened in the **ReSowRS** directory enter the following command:

```
>>> python master_processor.py
```

## 3. Documentation

[readthedocs](https://resowrs.readthedocs.io/en/latest/)
