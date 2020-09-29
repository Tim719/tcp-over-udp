#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/select.h>
#include <sys/time.h>

#define RCVSIZE 1024

int tcp_over_udp_accept(int fd, int data_port, struct sockaddr_in *client)
{
  printf("Waiting for connection\n");
  char buffer[32];
  int n;
  socklen_t client_size = sizeof(struct sockaddr);

  char SYN_ACK[16];
  sprintf(SYN_ACK, "SYN-ACK-%d\n", data_port);

  memset(buffer, 0, 32);
  n = recvfrom(fd, &buffer, 32, 0, (struct sockaddr *)client, &client_size);

  if (strcmp(buffer, "SYN\n") != 0)
  {
    perror("Connection must start with SYN\n");
    return -1;
  }
  printf("SYN received\n");

  n = sendto(fd, SYN_ACK, strlen(SYN_ACK), 0, (struct sockaddr *)client, client_size);
  if (n < 0)
  {
    perror("Unable to send SYN-ACK\n");
    return -1;
  }
  printf("SYN-ACK sent\n");

  memset(buffer, 0, 32);

  n = recvfrom(fd, &buffer, 32, 0, (struct sockaddr *)client, &client_size);
  if (strcmp(buffer, "ACK\n") != 0)
  {
    perror("ACK not received\n");
    return -1;
  }
  printf("ACK received. Connected\n");

  return data_port;
}

int main(int argc, char *argv[])
{
  printf("Henlo\n");
  struct sockaddr_in server_address, client;
  socklen_t client_size = sizeof(struct sockaddr);
  int optval = 1; // To set SO_REUSEADDR to 1
  int port = 0;
  int data_port = 0;
  int recvsize = 0;
  char buffer[RCVSIZE];
  pid_t fork_pid = 0;

  if (argc != 3)
  {
    printf("USAGE: server <control_port> <data_port>\n");
    return 0;
  }

  port = atoi(argv[1]);
  data_port = atoi(argv[2]);

  if (port < 0 || data_port < 0)
  {
    printf("Port number must be greater than 0\n");
  }

  //create socket
  int server_udp = socket(AF_INET, SOCK_DGRAM, 0);
  setsockopt(server_udp, SOL_SOCKET, SO_REUSEADDR, (const void *)&optval, sizeof(int));

  //handle error
  if (server_udp < 0)
  {
    perror("Cannot create socket\n");
    return -1;
  }

  printf("Binding address...\n");

  server_address.sin_family = AF_INET;
  server_address.sin_port = htons(port);
  server_address.sin_addr.s_addr = htonl(INADDR_ANY);

  if (bind(server_udp, (struct sockaddr *)&server_address, sizeof(server_address)) == -1)
  {
    perror("UDP Bind failed\n");
    close(server_udp);
    return -1;
  }

  while (1)
  {
    printf("Accepting connections...\n");

    // Serveur UDP
    int portnumber = tcp_over_udp_accept(server_udp, data_port, &client);

    if (portnumber == 0)
    {
      printf("Everything is fine my friend\n");
    }

    data_port++;

    // Forking to serve new clients

    fork_pid = fork();

    if (fork_pid < 0)
    {
      perror("Error forking process\n");
      return -1;
    }

    if (fork_pid == 0)
    {
      // Child process here
      close(server_udp);

      server_address.sin_port = htons(portnumber);
      server_udp = socket(AF_INET, SOCK_DGRAM, 0);
      setsockopt(server_udp, SOL_SOCKET, SO_REUSEADDR, (const void *)&optval, sizeof(int));

      if (bind(server_udp, (struct sockaddr *)&server_address, sizeof(server_address)) == -1)
      {
        perror("UDP Data connection bind failed\n");
        close(server_udp);
        return -1;
      }

      // Starting here: we are connected to a client
      while (1)
      {
        memset(&buffer, 0, RCVSIZE);
        printf("Waiting for new message\n");
        recvsize = recvfrom(server_udp, &buffer, RCVSIZE, 0, (struct sockaddr *)&client, &client_size);

        if (strcmp(buffer, "FIN\n") == 0)
        {
          printf("FIN received from client. Closing connection\n");
          break;
        }

        printf("Client(%d)>%s\n", recvsize, buffer);
        recvsize = sendto(server_udp, &buffer, strlen(buffer), 0, (struct sockaddr *)&client, client_size);

        if (recvsize < 0)
        {
          perror("Error sending message\n");
          return -1;
        }

        printf("Message sent %d\n", recvsize);
      }
      close(server_udp);
      exit(0);
    }
    else
    {
      printf("Child process started at PID %d\n", fork_pid);
    }
  }

  /*
  while (1) {
    printf("Accepting connections on port %d\n", port);
    
    // Serveur UDP
    memset(buffer,0,RCVSIZE);

    msgSize = recvfrom(server_udp, &buffer, RCVSIZE, 0, (struct sockaddr *) &client, &client_size);

    if (strcmp(buffer, "SYN")) {
      printf("SYN received\n");
      msgSize = sendto(server_udp, &SYN_ACK, strlen(SYN_ACK), 0, (struct sockaddr *) &client, client_size); 
      printf("SYN-ACK sent: %s\n", SYN_ACK);
      memset(buffer,0,RCVSIZE);
      msgSize = recvfrom(server_udp, &buffer, RCVSIZE, 0, (struct sockaddr *) &client, &client_size);
      if (strcmp(buffer, "ACK")) {
        printf("ACK received. Connected");
      }
    }

    if (msgSize < 0) {
      break;
    }

    if (msgSize > 0) {
      printf("UDP> %s",buffer);
      msgSize = sendto(server_udp, &buffer, strlen(buffer), 0, (struct sockaddr *) &client, client_size);
      printf("%d bytes sent\n", msgSize);
    }
  }
  */

  printf("Closing UDP server\n");
  close(server_udp);
  return 0;
}
