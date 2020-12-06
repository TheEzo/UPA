# UPA Project (COVID-19)
* **Dotaz A**: vytvořte popisné charakteristiky pro alespoň 4 údaje (např. věk, pohlaví, okres, zdrojnákazy) z datové sady COVID-19: Přehled osob s prokázanou nákazou dle hlášení krajskýchhygienických stanic (využijte krabicové grafy, histogramy, atd.).
* **Dotaz B**: určete vliv počtu nemocných a jeho změny v čase na sousední okresy (aneb zjistětejak se šíří nákaza přes hranice okresů).
* **Vlastní dotaz**: určete vliv věku na délku nemoci a úmrtnost

## Requirements
 - Docker 18.03+ (including docker-compose etc.)
 - Python 3.6+ 
 - virtualenv

## Usage
```bash
$ ./run.sh [-h] [-b] [-sqlr] [-esr]
```
 - ```-h``` prints help
 - ```-b``` forces container to rebuild 
 - ```-sqlr``` forces MySQL db to recreate
 - ```-esr``` forces Elastic Search db to recreate

## Authors
 - Petr Kapoun ([xkapou04](mailto:xkapou04@stud.fit.vutbr.cz))
 - Pavel Nováček ([xnovac16](mailto:xnovac16@stud.fit.vutbr.cz))
 - Tomáš Willaschek ([xwilla00](mailto:xwilla00@stud.fit.vutbr.cz))

## License
<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" /></a>


[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).



 