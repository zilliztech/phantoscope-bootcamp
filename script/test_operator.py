import argparse
import logging
import grpc
import rpc.rpc_pb2 as pb
import rpc.rpc_pb2_grpc as rpc_pb2_grpc
logging.basicConfig(level=logging.INFO)


def identity(endpoint):
    try:
        with grpc.insecure_channel(endpoint) as channel:
            stub = rpc_pb2_grpc.OperatorStub(channel)
            res = stub.Identity(pb.IdentityRequest())
            return {
                "name": res.name,
                "endpoint": res.endpoint,
                "type": res.type,
                "input": res.input,
                "output": res.output,
                "dimension": res.dimension,
                "metric_type": res.metricType
            }
    except Exception as e:
        logging.error("identity request error dut to %s", str(e))
        raise e


def health(endpoint):
    try:
        with grpc.insecure_channel(endpoint) as channel:
            stub = rpc_pb2_grpc.OperatorStub(channel)
            res = stub.Healthy(pb.HealthyRequest())
            return res.healthy
    except Exception as e:
        logging.error("health request error dut to %s", str(e))
        raise e


def execute(endpoint, datas=[], urls=[]):
    try:
        with grpc.insecure_channel(endpoint) as channel:
            stub = rpc_pb2_grpc.OperatorStub(channel)
            res = stub.Execute(pb.ExecuteRequest(urls=urls, datas=datas))
            return [list(x.element) for x in res.vectors], res.metadata
    except Exception as e:
        logging.error("execute request error dut to %s", str(e))
        raise e


if __name__ == '__main__':
    test_url = 'http://a3.att.hudong.com/14/75/01300000164186121366756803686.jpg'
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--endpoint", type=str, help="test grpc service in given port",
                        default="127.0.0.1:50001", dest="endpoint")
    args = parser.parse_args()
    endpoint = args.endpoint
    logging.info("Begin to test: endpoint-%s" % endpoint)
    logging.info("Endpoint information: ", identity(endpoint))
    logging.info("Endpoint health: ", health(endpoint))

    vector, data = execute(endpoint, urls=[test_url])
    logging.info("Result :\n  vector size: %d;  data size: %d" % (len(vector), len(data)))

    if len(vector) > 0:
        logging.info("  vector dim: ", len(vector[0]))

    logging.info("All tests over.")
    exit()
