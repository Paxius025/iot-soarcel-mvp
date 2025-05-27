from concurrent import futures
import grpc
import time
import pandas as pd
import logging

import model_pb2
import model_pb2_grpc
from grpc_reflection.v1alpha import reflection
from gru_model import GRUModel  # <-- Import GRUModel
from et_model import ETModel
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [gRPC] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ModelServiceServicer(model_pb2_grpc.ModelServiceServicer):
    def __init__(self):
        self.gru = GRUModel()
        self.et_model = ETModel()

    def Predict(self, request, context):
        logger.info(
            f"Received request from device: {request.device_id}\n"
            f"  IRRADIATION: {request.irradiation}\n"
            f"  MODULE_TEMPERATURE: {request.module_temperature}\n"
            f"  AMBIENT_TEMPERATURE: {request.ambient_temperature}\n"
            f"  TIMESTAMP: {request.timestamp}"
        )
        
        # 1. Step 1: Receive input
        input_df = pd.DataFrame([{
            'IRRADIATION': request.irradiation,
            'MODULE_TEMPERATURE': request.module_temperature,
            'AMBIENT_TEMPERATURE': request.ambient_temperature
        }])

        try:
            # 2. Step 2: Forecast ahead with GRU
            forecast_array = self.gru.forecasting(input_df)  # -> np.ndarray (3,)
            
            # 3. Step 3: Create new DataFrame for ETModel
            forecast_df = pd.DataFrame([{
            'IRRADIATION': forecast_array[0],
            'MODULE_TEMPERATURE': forecast_array[1],
            'AMBIENT_TEMPERATURE': forecast_array[2]
            }])

            # 4. Step 4: Use ETModel for final prediction
            prediction = self.et_model.predict(forecast_df)  # → Expected to get array or scalar

            logger.info(f"Final prediction (ETModel): {prediction}")

        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return model_pb2.AIResponse(status="error", score=0.0)

        # 5. Step 5: Return the result via gRPC
        final_score = float(prediction[0])

        response = model_pb2.AIResponse(
            status="ok",
            score=model_pb2.AIScores(  
                IRRADIATION=float(forecast_array[0]),
                MODULE_TEMPERATURE=float(forecast_array[1]),
                AMBIENT_TEMPERATURE=float(forecast_array[2])
            ),
            final_score=final_score 
        )

        logger.info(f"Sending response: {response}")
        return response

# gRPC Service setup
SERVICE_NAMES = (
    model_pb2.DESCRIPTOR.services_by_name['ModelService'].full_name,
    reflection.SERVICE_NAME,
)

def serve():
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        model_pb2_grpc.add_ModelServiceServicer_to_server(ModelServiceServicer(), server)
        reflection.enable_server_reflection(SERVICE_NAMES, server)
        server.add_insecure_port('[::]:50051')
        server.start()
        logger.info("Server started on port 50051")
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        logger.info("Server shutting down")
        server.stop(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == '__main__':
    serve()