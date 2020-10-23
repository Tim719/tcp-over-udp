EXEC = serveur1-Narvalo serveur2-Narvalo serveur3-Narvalo
SRC= $(EXEC:=.py)
OUT= ../bin

all: $(EXEC)

%: %.py
	cp $< $(OUT)/$@
	cp helpers.py $(OUT)/helpers.py


clean: 
	\rm -rf $(foreach binfile,$(EXEC),$(OUT)/$(binfile)) $(OUT)/helpers.py