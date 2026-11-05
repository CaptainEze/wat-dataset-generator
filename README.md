# WAT Dataset Generator

An open collection of real crude oil wax measurements, plus a tool that makes realistic extra examples from physics.

## The problem

Crude oil carries dissolved wax. When the oil cools in a pipeline, that wax starts to turn solid at a certain temperature. This is called the **wax appearance temperature (WAT)**. Below it, wax builds up on pipe walls and can block flow. Operators need to know the WAT early, but measuring it takes lab equipment and time, and the numbers are scattered across papers, theses and company reports.

## What this repo is for

Predicting WAT from simple, widely available properties of a crude: its density (API gravity), pour point, wax content and viscosity. A prediction model needs examples to learn from, and public WAT data is scarce and messy. This repo tackles that in three parts.

### 1. A cleaned, sourced WAT dataset

About 350 measurements on roughly 260 oils from around the world, taken from published papers, theses, operator reports and assay sheets. Every row records where it came from, how the WAT was measured, and how far to trust it. Rows from the same oil or field are tagged together so a model is never tested on an oil it has already seen. Earlier versions are kept so the build-up can be traced.

Nothing here is private or paid. Where a source could not be opened, it is logged and left out.

### 2. A knowledge base from the literature

Equations, rules of thumb and facts linking WAT to other crude properties, pulled from several hundred papers and reports, with the citations between them mapped as a network. It records how wax physics works, how different lab methods read different WAT values for the same oil, and how density, viscosity and pour point relate.

### 3. A synthetic data generator

Because real data is limited, the generator invents plausible crude oils and works out their WAT using wax melting physics. It then adds the quirks of each lab method, such as the different detection limits of microscopy and calorimetry. The invented examples can be used to practise on, or the physics estimate can be fed to a model as an extra clue.

## What we found

The generator was tested honestly: the real oils held back for testing were never used to tune it.

- Synthetic examples on their own do not make a better model.
- Using the physics estimate as an extra input does help. In the test it lowered the typical error of one model (Extra Trees) from about 9.4 °C to 8.6 °C, an improvement of roughly 0.8 °C.
- That test used only 77 measurements, so treat it as a promising sign, not a final answer.

Known weak points are listed in `docs/knowledge_study.md`, including parts of the physics that still need better sources.

## Using it

Install the packages in `requirements.txt`, then from the `src` folder:

```
python main.py                  # run the full workflow
python main.py --objective 4 --fast
python generate.py --mode forward --n 5000 --out ../data/synthetic/my_data.csv
```

The generator can invent whole crudes (`forward`) or take real crudes that lack a WAT and simulate their WAT (`anchored`). You can also ask for the readings of one lab method only, for example `--method CPM`.

## Where things are

- `data/master/` has the dataset. Start with `wat_master.csv`.
- `data/harvest/` holds the raw findings from each round of collection, with source logs.
- `knowledge/` is the literature knowledge base.
- `docs/` explains how the dataset was built, what was tried and what the results were.
- `src/` is the code.

## Data rules

- Public sources only.
- Each row has a trust level from A (operator or lab report) down to D (unverified), plus P for pending and X for excluded rows such as live oil or blends.
- Cloud point values are kept but marked as a weaker substitute for WAT.
- Synthetic rows are never used as test data.

## Contributing

If you have a public WAT measurement that is not here, please open an issue with the source. A value needs a link or citation, the method used, and at least some bulk properties to be useful.
