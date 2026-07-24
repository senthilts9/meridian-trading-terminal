CXX ?= g++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra -static

TARGET = cmle
SOURCES = main.cpp liquidation_model.cpp

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(SOURCES) liquidation_model.hpp
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCES)

# Runs the model against real captured data from this project's testnet run
# and checks it lands within 0.1% of the exchange-reported value.
test: $(TARGET)
	./$(TARGET) --side SHORT --entry 66000 --size 0.00023 \
		--collateral 100001.00961987 --imf-base 0.02 --mmf-factor 0.5 \
		--actual 430351430.25096846

clean:
	rm -f $(TARGET) $(TARGET).exe
