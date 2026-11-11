# SEPTA Regional Rail stations

**One-line summary:** SEPTA's own station-by-line table for Regional Rail: 155 rows (154 distinct stations), with location, accessibility, amenities, ridership counts, and the political districts SEPTA assigns to each.

## Source

- **Original source:** SEPTA, [Regional Rail Stations layer](https://services2.arcgis.com/9U43PSoL47wawX5S/arcgis/rest/services/Regional_Rail_Stations/FeatureServer/0) (public ArcGIS FeatureServer)
- **Pulled on:** 2026-11-10
- **Geography:** SEPTA Regional Rail network, including stations in Delaware (New Castle) and New Jersey (Mercer)
- **Time period covered:** SEPTA does not state a date or counting period for the ridership fields in the layer

## Processing

Every attribute SEPTA publishes was kept as is. Only the internal `OBJECTID` and `GlobalID` columns were dropped, and rows were sorted by line then station. Script: [`pipelines/septa_regional_rail_stations/fetch.py`](../../../pipelines/septa_regional_rail_stations/fetch.py).

## Files

| File | Format | Description |
|---|---|---|
| `septa-regional-rail-stations.csv` | CSV | One row per station per line, 80 columns |

## Columns

Column names are SEPTA's, unchanged. The main groups:

| Columns | Description |
|---|---|
| `Line_Name`, `Station_Name`, `Stop_ID` | Line and station. `Line_Name` is `Joint` for 12 stations shared between lines. |
| `Latitude`, `Longitude` | WGS84 location |
| `Municipality`, `County`, `City`, `State`, `Zip`, address fields | SEPTA's location fields. See caveats. |
| `Fare_Zone`, `Owner`, `Property_Status`, `Mile_Post` | Operations |
| `ADA_Accessible`, `Platform_Type`, `Elevators`, `Escalators` | Accessibility and platform |
| Parking, bike, shelter, restroom and similar amenity columns | Station amenities |
| `Minority_Area`, `Low_Income_Area`, `Minority_Low_Income_Area` | SEPTA's equity flags |
| `PA_US_Congressional_District`, `PA_State_Senate_District`, `PA_State_House_District`, `Philadelphia_City_Council_Distr` | Districts as assigned by SEPTA |
| `Weekday_*`, `Saturday_*`, `Sunday_*`, `Total_*` | Boardings, alightings and trips by day type and direction |

## Known gaps and caveats

- **County is wrong for some stations.** Bala, Cynwyd and Rosemont are in Montgomery County but SEPTA lists `Philadelphia`. The two stations named Highland carry inconsistent municipality and county pairs. Do not use `County` or `Municipality` for any join without checking them against a real boundary layer. [Regional Rail stations by district](../regional-rail-station-districts/) has corrected values from Census boundaries.
- **Districts may not be current.** We have not checked SEPTA's district fields against the post-2022 legislative maps. Treat them as SEPTA's claim until a point-in-polygon check is done.
- **Not one row per station.** North Philadelphia appears twice (Chestnut Hill West and Trenton lines, same `Stop_ID`), so there are 155 rows but 154 distinct stations.
- **One station has no ridership.** 9th Street (Lansdale/Doylestown Line) has empty ridership fields.
- **Ridership period unknown.** The layer does not document when counts were taken or whether `Total_Annual_*` is a true annual figure. Check against SEPTA's published ridership before citing.

## License

CC BY 4.0. Please credit Transit Forward Philly and SEPTA.
