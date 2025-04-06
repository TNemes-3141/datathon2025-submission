|Client feature|Type|Examples|what to do if not given|
|-------------|----|--------|------------------------|
|Degrees|one-hot encoded|[Bachelor,other higher,Master,PhD,Postdoc] If degree is obtained, set to 1, otherwise 0|[0,0,0,0,0] (if no degrees)|
|Maximum prestige of university degrees|range|1–5|0|
|seniority score|Number|Junior=1,Senior=2,Manager=3,Director=4,C-level=5,Chairman=6|0|
|inheritance seniority score|Number|Junior=1,Senior=2,Manager=3,Director=4,C-level=5,Chairman=6|0|
|Employment history progressing?|bool|If the general trend is upward, then true; if stagnating or declining, false|false|
|Chronological consistency in education|bool|Whether education progress is consistent in regard to graduation years and age||
|Chronological consistency in carreer|bool|Whether carreer progress is consistent in regard to employment durations and age||
|Founded company?|bool|||
|company sold|Number||0|
|Marital status|bool|Has been married at one point or not||
|Number of children|Number|||
|Salary consistency|bool array|Whether salary numbers are sensible in regard to the position held and the time of employment|[]|