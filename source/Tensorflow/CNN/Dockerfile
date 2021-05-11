#FROM jupyter/scipy-notebook:17aba6048f44
FROM jupyter/scipy-notebook:latest

RUN pip install tqdm
RUN pip install plotly
RUN pip install tensorflow
#RUN conda install --channel defaults conda python=3.6 --yes
#RUN conda update conda --channel defaults --yes
RUN conda install py-xgboost