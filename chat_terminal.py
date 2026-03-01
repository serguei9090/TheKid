import socket
import sys

def main():
    print("====================================================")
    print("   THE KID - NEURAL CHAT INTERFACE (DECOUPLED)     ")
    print("====================================================")
    print("Type 'exit' or 'quit' to close the connection.")
    print("-" * 50)

    host = "127.0.0.1"
    port = 5050

    while True:
        try:
            user_input = input("USER: ")
            if not user_input.strip():
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Closing interface...")
                break
            
            # Create a short-lived connection for this turn
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(10) # 10 second timeout for Teacher thoughts
            
            try:
                client.connect((host, port))
                client.send(user_input.encode("utf-8"))
                
                response = client.recv(4096).decode("utf-8")
                print(response)
                print("-" * 50)
                
                if "shutting down" in response.lower():
                    print("Brain server has been stopped. Press any key to exit.")
                    break
            except ConnectionRefusedError:
                print("ERROR: Connection Refused. Is the Brain (main.py) running in another terminal?")
            except socket.timeout:
                print("ERROR: The Brain is taking too long to think. Check the server terminal for errors.")
            finally:
                client.close()

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Interface Error: {e}")

if __name__ == "__main__":
    main()
