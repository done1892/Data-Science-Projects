#CLIMATE CHANGE
library(MASS)
library(plyr) 
library(ggplot2)
library(knitr)
library(kableExtra)
library(GGally)
df <- read.csv('D:/uni/DECISION MODELS/Asignment1/Asignment1/Dataset/ClimateChange.csv')
head(df)
summary(df)
#COLLINEARITà
pairs(df)
#RICAVO TRAIN E TEST
train <- subset(df, Year < 2007)
test <- subset(df, Year >= 2007)
summary(train)
#REGRESSIONE SU TRAIN
TrainReg = lm(formula = Temp ~ MEI + CO2 + CH4 + N2O +CFC.11 + CFC.12 + TSI + Aerosols, data = train)
summary(TrainReg)
cor(df$N2O, df$CH4)
cor(df$N2O, df$CO2)
cor(df$N2O, df$CFC.12)
cor(df$CFC.11, df$CH4)
cor(df$CFC.11, df$CO2)
cor(df$N2O, df$CFC.11)
cor(df$CFC.11, df$CFC.12)
TrainReg2 = lm(formula = Temp ~ MEI + TSI + Aerosols + N2O, data = train)
summary(TrainReg2)
TempPredict = predict(TrainReg2, newdata = test)
str(TempPredict)
TempPredict
SSE = sum((test$Temp - TempPredict)^2) #residui
SST = sum((test$Temp - mean(df$Temp))^2)
Rquadro = 1 - (SSE/SST)
Rquadro