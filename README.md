# A Little Item Database

## intro

![demo-3](img/demo-3.png)

## run

```shell
# default: genshin_materials
uv run cli.py
uv run cli.py starrail_materials
```

or

```powershell
.\genshin_materials.cmd
.\starrail_materials.cmd
```

## test

```shell
uv run test.py
```

## appendix

### change data

![demo-1](img/demo-1.png)
![demo-2](img/demo-2.png)

### filter & sort

![demo-3](img/demo-3.png)

### use json

```shell
uv run table-to-json.py genshin_materials
# change json data
uv run json-to-table.py genshin_materials
uv run delete-backup.py genshin_materials
```
