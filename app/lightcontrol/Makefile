
WS281X_DIR=rpi_ws281x
EXE=setlight
SRC=$(EXE).c

$(EXE): $(SRC) $(WS281X_DIR)/libws2811.a
	gcc -I$(WS281X_DIR) -o $(EXE) $(SRC) $(WS281X_DIR)/libws2811.a

$(WS281X_DIR)/libws2811.a: $(WS281X_DIR)/SConscript
	cd $(WS281X_DIR) && scons libws2811.a

install: $(EXE)
	install -o root -g staff -t /usr/local/bin -m 'u=rwxs,go=rx-s' $(EXE)

