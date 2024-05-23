import boto3


def download_s3_range(bucket_name, object_key, byte_range, local_file_path):
    """
    Download a specific byte range of an S3 object.

    Parameters:
    - bucket_name: Name of the S3 bucket.
    - object_key: Key of the object in the S3 bucket.
    - byte_range: Tuple (start, end) specifying the byte range.
    - local_file_path: Local path to save the downloaded content.
    """
    s3 = boto3.client("s3")

    # Construct the Range header value
    range_header = f"bytes={byte_range[0]}-{byte_range[1]}"

    try:
        # Perform the S3 GET operation with Range header
        response = s3.get_object(Bucket=bucket_name, Key=object_key, Range=range_header)

        # Verify status code and headers
        if response["ResponseMetadata"]["HTTPStatusCode"] == 206:
            content_range = response.get("ContentRange")
            print(f"Content-Range received: {content_range}")

            # Calculate the actual bytes returned
            actual_bytes = response["ContentLength"]
            expected_bytes = byte_range[1] - byte_range[0] + 1

            if actual_bytes == expected_bytes:
                print("Successfully received the correct range.")

                # Write the body of the response to a local file
                with open(local_file_path, "wb") as f:
                    f.write(response["Body"].read())
                print("Downloaded part of the file successfully.")
            else:
                print(f"Expected {expected_bytes} bytes, but got {actual_bytes} bytes.")
        else:
            print("Did not receive partial content as expected.")

    except boto3.exceptions.Boto3Error as e:
        print(f"An error occurred: {e}")
