#include "funcs.h"

int tcp_over_udp_connect(int fd, struct sockaddr_in *server)
{
  char msg[32];
  int n;
  socklen_t server_len = sizeof(struct sockaddr);
  printf("Sending SYN\n");

  n = sendto(fd, "SYN\n", 4, 0, (struct sockaddr *)server, server_len);
  if (n < 0)
  {
    perror("Error sending SYN packet\n");
    return -1;
  }

  printf("SYN sent\n");

  memset(msg, 0, 32);
  n = recvfrom(fd, &msg, 32, 0, (struct sockaddr *)server, &server_len);

  if (n < 0)
  {
    perror("Error receiving SYN-ACK\n");
    return -1;
  }

  if (strncmp(msg, "SYN-ACK", 7) != 0)
  {
    perror("SYN-ACK not received\n");
    return -1;
  }

  printf("SYN-ACK received\n");

  char *data_port = malloc(6);

  strncpy(data_port, msg + 8, 6);

  printf("Sending ACK\n");
  n = sendto(fd, "ACK\n", 4, 0, (struct sockaddr *)server, server_len);
  if (n < 0)
  {
    perror("Error sending ACK packet\n");
    return -1;
  }

  printf("ACK sent\n");
  return atoi(data_port);
}

int tcp_over_udp_accept(int fd, int data_port, struct sockaddr_in *client)
{
  printf("Waiting for connection\n");
  char buffer[32];
  int n;
  socklen_t client_size = sizeof(struct sockaddr);

  char SYN_ACK[16];
  sprintf(SYN_ACK, "SYN-ACK-%d\n", data_port);

  memset(buffer, 0, 32);
  n = recvfrom(fd, &buffer, 32, 0, (struct sockaddr *) client, &client_size);

  if (strcmp(buffer, "SYN\n") != 0)
  {
    perror("Connection must start with SYN\n");
    return -1;
  }
  printf("SYN received\n");

  n = sendto(fd, SYN_ACK, strlen(SYN_ACK), 0, (struct sockaddr *) client, client_size);
  if (n < 0)
  {
    perror("Unable to send SYN-ACK\n");
    return -1;
  }
  printf("SYN-ACK sent\n");

  memset(buffer, 0, 32);

  n = recvfrom(fd, &buffer, 32, 0, (struct sockaddr *) client, &client_size);
  if (strcmp(buffer, "ACK\n") != 0)
  {
    perror("ACK not received\n");
    return -1;
  }
  printf("ACK received. Connected\n");

  return data_port;
}

int safe_send(int fd, char* buffer, struct sockaddr_in *client, int seq_number)
{
  socklen_t client_size = sizeof(struct sockaddr);

  int msglen = sendto(fd, buffer, strlen(buffer), 0, (struct sockaddr *) client, client_size);

  if (msglen < 0)
  {
    perror("Error sending message\n");
    return -1;
  }

  char ack_buffer[12];

  int ack_msglen = recvfrom(fd, ack_buffer, 12, 0, (struct sockaddr *) client, &client_size);

  if (ack_msglen < 0)
  {
    perror("Error receiving ACK\n");
    return -1;
  }

  printf("(safe_send) ACK: %s\n", ack_buffer);

  return msglen;
}

int safe_recv(int fd, char* buffer, struct sockaddr_in *client, int seq_number)
{
  socklen_t client_size = sizeof(struct sockaddr);

  int msglen = recvfrom(fd, buffer, MAX_DGRAM_SIZE, 0, (struct sockaddr *) client, &client_size);

  if (msglen < 0)
  {
    perror("Error receiving message\n");
    return -1;
  }

  printf("(safe_recv) Message received: %s\n", buffer);

  char ack[12];
  memset(ack, 0, 12);

  int new_seq_number = seq_number + msglen;

  sprintf(ack, "ACK-%06d\n", new_seq_number);

  int ack_msglen = sendto(fd, ack, strlen(ack), 0, (struct sockaddr *) client, client_size);

  if (ack_msglen < 0)
  {
    perror("Error sending ACK\n");
    return -1;
  }

  return msglen;
}
