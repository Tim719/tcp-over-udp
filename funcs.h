#ifndef SERVER_FUNCS_H
#define SERVER_FUNCS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/time.h>

#define MAX_DGRAM_SIZE 1000

int tcp_over_udp_connect(int fd, struct sockaddr_in *server);

int tcp_over_udp_accept(int fd, int data_port, struct sockaddr_in *client);

int safe_send(int fd, char* buffer, struct sockaddr_in *client, int seq_number);

int safe_recv(int fd, char* buffer, struct sockaddr_in *client, int seq_number);

#endif