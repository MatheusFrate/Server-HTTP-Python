import os
import socket
import threading
import time

class HTTPServer:
    def __init__(self, host, port, base_dir):
        self.host = host
        self.port = port
        self.base_dir = base_dir
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) ## Af_inet = representa a familia  de endereços ipv4, sock_stream = interface para o tcp


    def log(self,timestamp,  address, requisicao, status): #abre o arquivo de log, e escreve os dados informados
        with open("log.txt", "a") as log_file:
            log_file.write(f"{timestamp} - {address[0]}:{address[1]} - [{requisicao}] - {status}\n")
            print(f"{timestamp} - {address[0]} - [{requisicao}] - {status}")


    def send_response(self, client, status, body, file_path):
        file_extension = os.path.splitext(file_path)[1] if file_path else ""

        if file_extension == ".html":
            content_type = "text/html"
        elif file_extension == ".css":
            content_type = "text/css"
        elif file_extension == ".js":
            content_type = "application/javascript"
        else:
            content_type = "text/plain"

        headers = f"HTTP/1.1 {status}\r\nContent-Type: {content_type}\r\nContent-Length: {len(body)}\r\n\r\n"
        client.send(headers.encode())  # Envia os cabeçalhos primeiro
        if isinstance(body, str):
            # Se o corpo estiver em string, codifique-a em bytes para enviar
            client.send(body.encode())
            return
        else:
            client.send(body)
            return


    
    def handle_get(self, client, path): #detecta se existe uma pagina valida
        file_path = os.path.join(self.base_dir, path.lstrip("/")) 
        if not os.path.exists(file_path) or path == "/":
            self.send_response(client, "404 Not Found", "Pagina nao encontrada :(", None)
            return "404 Pagina nao encontrada"
        with open(file_path, "rb") as file:
            content = file.read()
        self.send_response(client, "200 OK", content, file_path)
        return "200 ok"
        


    
    def handle_client(self, client, address):
        try:
            while True:
                request = client.recv(1024) # recebe a requisição
                if not request:
                    client.close()
                    break   #caso não veio nenhuma requisição, o while é finalizado

                request = request.decode().split("\r\n")
                method, path, _ = request[0].split(" ")
                timestamp = time.ctime()
                requisicao = f"{method} {path}"
            
                if method == "GET": # se a requisição for um get (unico metodo http implementado)
                    codigo_requisição = self.handle_get(client, path)
                    threading.Thread(
                        daemon=True,
                        target=self.log,
                        args=(timestamp,  address, requisicao, codigo_requisição)
                    ).start()# chama a função de log em uma thread
                else:
                    self.send_response(client, "502 Not Implemented", "Método não implementado", None)
                    threading.Thread(
                        daemon=True,
                        target=self.log,
                        args=(timestamp,  address, requisicao, "502 Nao implementado")
                    ).start() # chama a função de log em uma thread
        except socket.timeout as e: # em caso de timeout, lança a exceção e fecha a conexão com o cliente
            print(f"tempo limite excedido, a conexão com {address[0]}:{address[1]} foi finalizada\r\n")
            client.close()
        

    def start(self):
        self.server.bind((self.host, self.port))
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # configura o timeout para 20 segundos
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, 20000)
        self.server.listen(1)

        print('servidor iniciado, host %s:%s \n\n' % (self.host, self.port))

        while True:

            # esperando pela conexões
            client, address = self.server.accept()
            # gerando threads para cada conexão feita
            threading.Thread(
                daemon=True,
                target=self.handle_client,
                args=(client, address)# trata a requisição do cliente em uma thread
            ).start()




    def stop(self):
        self.server.close()
        print("Parando o servidor")


if __name__ == "__main__":
    base_dir = os.getcwd()
    server = HTTPServer("localhost", 8001, base_dir)
    server.start()