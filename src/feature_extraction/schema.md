|Client feature|Type|Examples|what to do if not given|
|-------------|----|--------|------------------------|
|Degrees|one-hot encoded|[Bachelor,other higher,Master,PhD,Postdoc] If degree is obtained, set to 1, otherwise 0|[0,0,0,0,0] (if no degrees)|
|Maximum prestige of university degrees|range|1–5|0|
|Savings|Number in dollar, log-scaled||0|
|Inheritance|Number in dollar, log-scaled||0|
|Real Estate|Number in dollar, log-scaled||0|
|company sold|Number in dollar, log-scaled||0|
|Last yearly salary|Number in dollar, log-scaled||interpolate current job otherwise 0|
|Average yearly salary|Number in dollar, log-scaled||0|
|Total salary|Number in dollar, log-scaled||0|
|Years worked|Number||0|
|seniority score|Number|Junior=1,Senior=2,Manager=3,Director=4,C-level=5,Chairman=6,|0|
|inheritance seniority score|Number|Junior=1,Senior=2,Manager=3,Director=4,C-level=5,Chairman=6,|0|
|Average tenure (employment duration per company)|Number||0|
|Employment history progressing?|bool|junior→senior→manager:true|false|
|Prestigious employer|binary|true/false|false|
|Age|number|||
|Nationality risk|bool|low risk=0,neutral=1,high risk=2,(based on list and HDI)|1|
|Investment Risk Profile|one hot encoding|low,middle,high||
|Type of mandate|one hot encoding|Advisory,Discretionary,||
|Investment Experience|one hot encoding|Experienced||
|Investment horizon|one hot encoding|Long-Term||
|Chronological consistency|bool|experience vs age,timeline vs age||
|Founded company?|bool|||
|Marital status|bool|Has been married at one point or not||
|Number of children|Number|||
|nationality||||
|profession||||
|Preferred Markets||||
|Consistency of professions with salaries|Number|Difference to median divided by median||
