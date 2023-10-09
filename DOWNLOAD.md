Dataset **SIIM-ACR Pneumothorax Segmentation 2019** can be downloaded in [Supervisely format](https://developer.supervisely.com/api-references/supervisely-annotation-json-format):

 [Download](https://assets.supervisely.com/supervisely-supervisely-assets-public/teams_storage/p/W/hC/reG4EjjbSIRIthzmJKnIQWj30LoxSWq0GfP4d8bT9nPyCIsAfPiKYRA4mexOGfGBQcuRYteKu0iapFZgvjhbUU4oKYAIf0daYysaKCqOVidEHOUGBm9xNW4UZjEQ.tar)

As an alternative, it can be downloaded with *dataset-tools* package:
``` bash
pip install --upgrade dataset-tools
```

... using following python code:
``` python
import dataset_tools as dtools

dtools.download(dataset='SIIM-ACR Pneumothorax Segmentation 2019', dst_dir='~/dataset-ninja/')
```
Make sure not to overlook the [python code example](https://developer.supervisely.com/getting-started/python-sdk-tutorials/iterate-over-a-local-project) available on the Supervisely Developer Portal. It will give you a clear idea of how to effortlessly work with the downloaded dataset.

The data in original format can be [downloaded here](https://www.kaggle.com/competitions/siim-acr-pneumothorax-segmentation/).