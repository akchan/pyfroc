# A sample script for AFROC analysis using RJafroc library
# 

# Install a required package
if (!require("RJafroc")) {
  install.packages("RJafroc")
}

library(RJafroc)

# Read the .xlsx file.
# sample_path = system.file("extdata", "Froc.xlsx", package = "RJafroc")
sample_path = "./sample_data/rjafroc_input.xlsx"
data <- DfReadDataFile(sample_path)

# Prepare variables
num_reader = length(data$descriptions$readerID)
num_modality = length(data$descriptions$modalityID)

# Perform JAFROC analysis
analysis_result <- StSignificanceTesting(data, FOM = "wAFROC1", method = "DBM")

# Print the result
print(analysis_result)

# Show the results for Random reader and random case (RRRC)
# which is common case for image interpletation
print("Read the estimated value, CILower, and CIUpper (lower and upper limits of confidence interval)")
print(analysis_result$RRRC$ciAvgRdrEachTrt)
print("p value:")
print(analysis_result$RRRC$FTests$p)

# Plot wAFROC (readers averaged)
plotModalityAvg = list()
plotReaderAvg = list()
for (i in c(1:num_modality)) {
  plotModalityAvg = append(plotModalityAvg, i)
  plotReaderAvg = append(plotReaderAvg, list(c(1:num_reader)))
}

plotAFROC_averaged = PlotEmpiricalOperatingCharacteristics(dataset=data,
                                                  trts=plotModalityAvg,
                                                  rdrs=plotReaderAvg,
                                                  opChType="wAFROC")
pdf("wAFROC_averaged.pdf")
plot(plotAFROC_averaged)
dev.off()


# Plot wAFROC (each reader)
plotModality = c(1:num_modality)
plotReader = c(1:num_reader)

plotAFROC_each = PlotEmpiricalOperatingCharacteristics(dataset=data,
                                                           trts=plotModality,
                                                           rdrs=plotReader,
                                                           opChType="wAFROC")
pdf("wAFROC_each_reader.pdf")
plot(plotAFROC_each_reader)
dev.off()

