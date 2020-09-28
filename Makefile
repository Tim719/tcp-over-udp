CFLAGS = -g -Wall -DDEBUG 
EXEC = server client
SRC= $(EXEC:=.c)
OBJ= $(SRC:.c=.o)

.PRECIOUS: $(OBJ)

all: $(EXEC)

%: %.o
	gcc  $^ -o $@

%.o: %.c
	gcc $(CFLAGS) -c $< -o $@

clean: 
	\rm -rf $(OBJ) *.o $(EXEC)