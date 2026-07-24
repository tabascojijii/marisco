# ---
# jupyter:
#   jupytext:
#     formats: ipynb,.pct.py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: python3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Field Definitions

# %% [markdown]
# MARIS data is distributed as **NetCDF4** files (primary format) and **CSV** files for database import. This reference lists all standard field definitions with their NetCDF variable names and CSV variable names. Fields marked `—` are not present in that format.
#
# The **MARISCO column** is the uppercase internal name used within the marisco curation pipeline.

# %% [markdown]
# ## Summary table
#
# | Field | MARISCO column | NetCDF variable | CSV variable |
# |---|---|---|---|
# | Sample quality | — | — | `sampquality` |
# | Sample type | `SAMPLE_TYPE` | *(group name)* | `samptype_id` |
# | Laboratory | `LAB` | `lab` | `lab_id` |
# | Latitude | `LAT` | `lat` | `latitude` |
# | Longitude | `LON` | `lon` | `longitude` |
# | Station | `STATION` | `station` | `station` |
# | Sample ID | `SMP_ID` | `smp_id` | `samplabcode` |
# | Profile ID | `PROFILE_ID` | — | `profile_id` |
# | Transect ID | — | — | `transect_id` |
# | Sampling depth | `SMP_DEPTH` | `smp_depth` | `sampdepth` |
# | Total depth | `TOT_DEPTH` | `tot_depth` | `totdepth` |
# | Begin period | `TIME` | `time` | `begperiod` |
# | End period | — | — | `endperiod` |
# | Nuclide | `NUCLIDE` | `nuclide` | `nuclide_id` |
# | Detection limit | `DL` | `dl` | `detection` |
# | Activity | `VALUE` | `value` | `activity` |
# | Uncertainty | `UNC` | `unc` | `uncertaint` |
# | Unit | `UNIT` | `unit` | `unit_id` |
# | Variable type | — | — | `vartype` |
# | Frequency | — | — | `freq` |
# | Range low detection | — | — | `rl_detection` |
# | Range low | — | — | `rangelow` |
# | Range upper | — | — | `rangeupp` |
# | Species | `SPECIES` | `species` | `species_id` |
# | Biological group | `BIO_GROUP` | `bio_group` | — |
# | Taxon name | `TAXONNAME` | — | `Taxonname` |
# | Taxon reported name | `TAXONREPNAME` | — | `TaxonRepName` |
# | Common name | — | — | `Commonname` |
# | Taxon rank | `TAXONRANK` | — | `Taxonrank` |
# | Taxon database | `TAXONDB` | — | `TaxonDB` |
# | Taxon database ID | `TAXONDBID` | — | `TaxonDBID` |
# | Taxon database URL | `TAXONDBURL` | — | `TaxonDBURL` |
# | Body part | `BODY_PART` | `body_part` | `bodypar_id` |
# | Slice up (top) | `TOP` | `top` | `sliceup` |
# | Slice down (bottom) | `BOTTOM` | `bottom` | `slicedown` |
# | Sediment type | `SED_TYPE` | `sed_type` | `sedtype_id` |
# | Sediment reported name | — | — | `SedRepName` |
# | Volume | — | — | `volume` |
# | Salinity | `SALINITY` | `salinity` | `salinity` |
# | Temperature | `TEMP` | `temperature` | `temperatur` |
# | Filtered | `FILT` | `filt` | `filtered` |
# | Filter pore size | — | — | `filtpore` |
# | Acidified | — | — | `acid` |
# | Oxygen | — | — | `oxygen` |
# | Sample area | — | — | `samparea` |
# | Dry weight | `DRYWT` | `drywt` | `drywt` |
# | Wet weight | `WETWT` | `wetwt` | `wetwt` |
# | Percent weight | `PERCENTWT` | — | `percentwt` |
# | Sampling method | `SAMP_MET` | `samp_met` | `sampmet_id` |
# | Drying method | — | — | `drymet_id` |
# | Preparation method | `PREP_MET` | `prep_met` | `prepmet_id` |
# | Counting method | `COUNT_MET` | `count_met` | `counmet_id` |
# | Reference | `REF_ID` | — | `ref_id` |
# | Reference note | — | — | `refnote` |
# | Sample note | — | — | `sampnote` |
# | Measurement note | — | — | `measurenote` |
# | Good for export | — | — | `gfe` |
# | Area | `AREA` | `area` | `area` |

# %% [markdown]
# ## Field descriptions

# %% [markdown]
# ## Sample Quality
#
# Indicates the quality assessment of the sample. Common values: G (Good), C (Caution), F (Fail).
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `sampquality` |
# | **CSV type** | string |

# %% [markdown]
# ## Sample Type
#
# Classifies the sample into one of four MARIS groups. In NetCDF4, sample type is encoded as the group name rather than a column variable. In CSV format it is an integer: 1 = SEAWATER, 2 = BIOTA, 3 = SEDIMENT, 4 = SUSPENDED.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | *(group name)* |
# | **NetCDF type** | string |
# | **CSV variable** | `samptype_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Laboratory
#
# Identifies the laboratory that processed and measured the sample.
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_lab.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_lab.xlsx) |
# | **NetCDF variable** | `lab` |
# | **NetCDF type** | integer |
# | **CSV variable** | `lab_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Latitude
#
# Decimal degrees, −90 to 90.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `lat` |
# | **NetCDF type** | float |
# | **CSV variable** | `latitude` |
# | **CSV type** | float |

# %% [markdown]
# ## Longitude
#
# Decimal degrees, −180 to 180.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `lon` |
# | **NetCDF type** | float |
# | **CSV variable** | `longitude` |
# | **CSV type** | float |

# %% [markdown]
# ## Station
#
# Name of the station where the sample was collected, as reported by the provider.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `station` |
# | **NetCDF type** | string |
# | **CSV variable** | `station` |
# | **CSV type** | string |

# %% [markdown]
# ## Sample ID
#
# The data provider's sample identifier. Stored verbatim when provided; a sequential integer is generated when absent.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `smp_id` |
# | **NetCDF type** | uint64 |
# | **CSV variable** | `samplabcode` |
# | **CSV type** | string |

# %% [markdown]
# ## Profile ID
#
# An identifier for linking samples that form part of a vertical sequence (profile). Provided as-is by the data provider.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `profile_id` |
# | **CSV type** | string |

# %% [markdown]
# ## Transect ID
#
# An identifier for linking samples that form part of a horizontal sequence (transect). Provided as-is by the data provider.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `transect_id` |
# | **CSV type** | string |

# %% [markdown]
# ## Sampling Depth
#
# Depth below the water surface at which the sample was taken, in metres. 0 = surface sample; −1 = depth not available.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `smp_depth` |
# | **NetCDF type** | float |
# | **CSV variable** | `sampdepth` |
# | **CSV type** | float |

# %% [markdown]
# ## Total Depth
#
# Total water column depth at the sampling location, in metres.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `tot_depth` |
# | **NetCDF type** | float |
# | **CSV variable** | `totdepth` |
# | **CSV type** | float |

# %% [markdown]
# ## Begin Period
#
# Date when sample collection began. If only a year is known, the date is set to 1 January of that year; if year and month are known, it is set to the 1st of that month.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `time` |
# | **NetCDF type** | int64 (seconds since 1970-01-01 00:00:00 UTC) |
# | **CSV variable** | `begperiod` |
# | **CSV type** | datetime string (yyyy-mm-dd hh:mm:ss) |

# %% [markdown]
# ## End Period
#
# Date when sample collection ended. Same date convention as Begin Period.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `endperiod` |
# | **CSV type** | datetime string (yyyy-mm-dd hh:mm:ss) |

# %% [markdown]
# ## Nuclide
#
# Identifies the measured radionuclide via a MARIS standard ID.
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_nuclide.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_nuclide.xlsx) |
# | **NetCDF variable** | `nuclide` |
# | **NetCDF type** | integer |
# | **CSV variable** | `nuclide_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Detection Limit
#
# Describes the status of the associated Activity value:
#
# - `1` (`=`) — measured value; an uncertainty should accompany it
# - `2` (`<`) — below detection limit; Activity holds the MDA or ISO 11929 detection limit
# - `3` (`ND`) — not detected; no activity value and no MDA reported
# - `4` (`DE`) — derived; Activity is an aggregation (mean, sum, etc.) of multiple samples
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_detectlimit.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_detectlimit.xlsx) |
# | **NetCDF variable** | `dl` |
# | **NetCDF type** | integer |
# | **CSV variable** | `detection` |
# | **CSV type** | integer |

# %% [markdown]
# ## Activity
#
# The measured activity or MDA for the nuclide. See Detection Limit for interpretation of this value.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `value` |
# | **NetCDF type** | float |
# | **CSV variable** | `activity` |
# | **CSV type** | float |

# %% [markdown]
# ## Uncertainty
#
# 1σ (k=1) measurement uncertainty, expressed in the same unit as Activity.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `unc` |
# | **NetCDF type** | float |
# | **CSV variable** | `uncertaint` |
# | **CSV type** | float |

# %% [markdown]
# ## Unit
#
# Unit of measurement for Activity and Uncertainty. MARIS stores seawater activities in Bq m⁻³ — values reported by providers in Bq L⁻¹ are converted (×1000).
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_unit.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_unit.xlsx) |
# | **NetCDF variable** | `unit` |
# | **NetCDF type** | integer |
# | **CSV variable** | `unit_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Variable Type
#
# Type of aggregation applied when Activity is not a single measurement. Common codes: AM (arithmetic mean), GM (geometric mean), MED (median), MAX, MIN.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `vartype` |
# | **CSV type** | string |

# %% [markdown]
# ## Frequency
#
# Regularity of sampling or measurement (e.g. daily, weekly, monthly).
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `freq` |
# | **CSV type** | string |

# %% [markdown]
# ## Range Low Detection
#
# Detection limit status of the Range Low value (same codes as Detection Limit). Used when Activity is an aggregated value.
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_detectlimit.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_detectlimit.xlsx) |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `rl_detection` |
# | **CSV type** | integer |

# %% [markdown]
# ## Range Low
#
# Minimum activity within an aggregated dataset, expressed in the unit given by Unit.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `rangelow` |
# | **CSV type** | float |

# %% [markdown]
# ## Range Upper
#
# Maximum activity within an aggregated dataset, expressed in the unit given by Unit.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `rangeupp` |
# | **CSV type** | float |

# %% [markdown]
# ## Species (BIOTA)
#
# Identifies the sampled species via a MARIS standard ID. When only a biological group is known (e.g. 'Fish'), the coarsest matching species entry in the LUT is used.
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_species.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_species.xlsx) |
# | **NetCDF variable** | `species` |
# | **NetCDF type** | integer |
# | **CSV variable** | `species_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Biological Group (BIOTA)
#
# Grouping of related species (e.g. crustaceans, molluscs, fish). Always derived from the `biogroup_id` column in `dbo_species.xlsx` — never assigned independently.
#
# | | |
# |---|---|
# | **Lookup table** | Derived from [dbo_species.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_species.xlsx) |
# | **NetCDF variable** | `bio_group` |
# | **NetCDF type** | integer |
# | **CSV variable** | — |
# | **CSV type** | — |

# %% [markdown]
# ## Taxon Name (BIOTA)
#
# Scientific name of the taxon, as defined in `dbo_species.xlsx`.
#
# | | |
# |---|---|
# | **Lookup table** | See `dbo_species.xlsx` |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `Taxonname` |
# | **CSV type** | string |

# %% [markdown]
# ## Taxon Reported Name (BIOTA)
#
# Taxon name as reported by the data provider (may differ from the accepted scientific name).
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `TaxonRepName` |
# | **CSV type** | string |

# %% [markdown]
# ## Common Name (BIOTA)
#
# Common (vernacular) name of the species or organism.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `Commonname` |
# | **CSV type** | string |

# %% [markdown]
# ## Taxon Rank (BIOTA)
#
# Rank of the taxon in the biological classification system (e.g. species, genus, family), as defined in `dbo_species.xlsx`.
#
# | | |
# |---|---|
# | **Lookup table** | See `dbo_species.xlsx` |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `Taxonrank` |
# | **CSV type** | string |

# %% [markdown]
# ## Taxon Database (BIOTA)
#
# Name of the external taxonomy database where this taxon is registered (e.g. WoRMS, ITIS).
#
# | | |
# |---|---|
# | **Lookup table** | See `dbo_species.xlsx` |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `TaxonDB` |
# | **CSV type** | string |

# %% [markdown]
# ## Taxon Database ID (BIOTA)
#
# Identifier for this taxon in the external taxonomy database.
#
# | | |
# |---|---|
# | **Lookup table** | See `dbo_species.xlsx` |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `TaxonDBID` |
# | **CSV type** | string |

# %% [markdown]
# ## Taxon Database URL (BIOTA)
#
# URL of the taxon record in the external taxonomy database.
#
# | | |
# |---|---|
# | **Lookup table** | See `dbo_species.xlsx` |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `TaxonDBURL` |
# | **CSV type** | string |

# %% [markdown]
# ## Body Part (BIOTA)
#
# Identifies the specific body part from which the sample was taken (e.g. flesh, whole animal, liver).
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_bodypar.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_bodypar.xlsx) |
# | **NetCDF variable** | `body_part` |
# | **NetCDF type** | integer |
# | **CSV variable** | `bodypar_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Slice Up / Top (SEDIMENT)
#
# Top of the sediment core interval relative to the water–sediment interface, in cm.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `top` |
# | **NetCDF type** | float |
# | **CSV variable** | `sliceup` |
# | **CSV type** | float |

# %% [markdown]
# ## Slice Down / Bottom (SEDIMENT)
#
# Bottom of the sediment core interval relative to the water–sediment interface, in cm.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `bottom` |
# | **NetCDF type** | float |
# | **CSV variable** | `slicedown` |
# | **CSV type** | float |

# %% [markdown]
# ## Sediment Type (SEDIMENT)
#
# Classification of sediment according to the Udden–Wentworth scale.
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_sedtype.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_sedtype.xlsx) |
# | **NetCDF variable** | `sed_type` |
# | **NetCDF type** | integer |
# | **CSV variable** | `sedtype_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Sediment Reported Name (SEDIMENT)
#
# Sediment name as reported by the data provider; stored verbatim.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `SedRepName` |
# | **CSV type** | string |

# %% [markdown]
# ## Volume
#
# Volume of the sample, in litres.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `volume` |
# | **CSV type** | float |

# %% [markdown]
# ## Salinity (SEAWATER)
#
# Salinity in practical salinity units (PSU). If the provider reports absolute salinity (g/kg), convert to PSU using [TEOS-10 guidelines](https://www.teos-10.org/).
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `salinity` |
# | **NetCDF type** | float |
# | **CSV variable** | `salinity` |
# | **CSV type** | float |

# %% [markdown]
# ## Temperature (SEAWATER)
#
# Water temperature at the time of sampling, in °C.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `temperature` |
# | **NetCDF type** | float |
# | **CSV variable** | `temperatur` |
# | **CSV type** | float |

# %% [markdown]
# ## Filtered (SEAWATER)
#
# Indicates whether the sample was filtered before measurement. In NetCDF4, stored as an integer: 1 = filtered (dissolved fraction), 2 = unfiltered (total).
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `filt` |
# | **NetCDF type** | integer (1 = filtered, 2 = unfiltered) |
# | **CSV variable** | `filtered` |
# | **CSV type** | string (Y = filtered, N = unfiltered, NA = not applicable) |

# %% [markdown]
# ## Filter Pore Size (SEAWATER)
#
# Pore size of the filter used, in µm.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `filtpore` |
# | **CSV type** | float |

# %% [markdown]
# ## Acidified
#
# Indicates whether the sample was acidified prior to analysis.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `acid` |
# | **CSV type** | string (A = acidified, NA = not acidified) |

# %% [markdown]
# ## Oxygen (SEAWATER)
#
# Dissolved oxygen concentration of the sample.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `oxygen` |
# | **CSV type** | float |

# %% [markdown]
# ## Sample Area (SEDIMENT)
#
# Surface area of the sediment sample, in cm².
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `samparea` |
# | **CSV type** | float |

# %% [markdown]
# ## Dry Weight (BIOTA)
#
# Dry weight of the sample, in grams.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `drywt` |
# | **NetCDF type** | float |
# | **CSV variable** | `drywt` |
# | **CSV type** | float |

# %% [markdown]
# ## Wet Weight (BIOTA)
#
# Wet weight of the sample, in grams.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | `wetwt` |
# | **NetCDF type** | float |
# | **CSV variable** | `wetwt` |
# | **CSV type** | float |

# %% [markdown]
# ## Percent Weight (BIOTA)
#
# Dry-to-wet weight ratio, expressed as a percentage: (dry weight / wet weight) × 100. Value must be between 0 and 100.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `percentwt` |
# | **CSV type** | float |

# %% [markdown]
# ## Sampling Method
#
# Method used to collect the sample.
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_sampmet.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_sampmet.xlsx) |
# | **NetCDF variable** | `samp_met` |
# | **NetCDF type** | integer |
# | **CSV variable** | `sampmet_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Drying Method
#
# Method used to dry the sample prior to analysis.
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_sampmet.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_sampmet.xlsx) |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `drymet_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Preparation Method
#
# Method used to prepare the sample for radioactivity measurement.
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_prepmet.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_prepmet.xlsx) |
# | **NetCDF variable** | `prep_met` |
# | **NetCDF type** | integer |
# | **CSV variable** | `prepmet_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Counting Method
#
# Analytical method used to measure radioactivity (e.g. gamma spectrometry, alpha spectrometry, LSC).
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_counmet.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_counmet.xlsx) |
# | **NetCDF variable** | `count_met` |
# | **NetCDF type** | integer |
# | **CSV variable** | `counmet_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Reference
#
# Identifies the source dataset or publication from which this record originates.
#
# | | |
# |---|---|
# | **Lookup table** | dbo_ref.xlsx (internal; not publicly distributed) |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `ref_id` |
# | **CSV type** | integer |

# %% [markdown]
# ## Reference Note
#
# Additional notes about the source reference.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `refnote` |
# | **CSV type** | string |

# %% [markdown]
# ## Sample Note
#
# Additional notes about the sample.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `sampnote` |
# | **CSV type** | string |

# %% [markdown]
# ## Measurement Note
#
# Additional notes about the measurement process.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `measurenote` |
# | **CSV type** | string |

# %% [markdown]
# ## Good for Export
#
# Flag indicating whether the record is suitable for export from the MARIS database.
#
# | | |
# |---|---|
# | **Lookup table** | No |
# | **NetCDF variable** | — |
# | **NetCDF type** | — |
# | **CSV variable** | `gfe` |
# | **CSV type** | string |

# %% [markdown]
# ## Area
#
# Named geographic region where the sample was collected.
#
# | | |
# |---|---|
# | **Lookup table** | [dbo_area.xlsx](https://github.com/franckalbinet/marisco/blob/main/nbs/files/lut/dbo_area.xlsx) |
# | **NetCDF variable** | `area` |
# | **NetCDF type** | integer |
# | **CSV variable** | `area` |
# | **CSV type** | integer |
