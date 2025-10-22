# Custom Spark image with pre-downloaded Delta Lake and dependencies
# This ensures all JARs are available even in offline/restricted environments

FROM bitnami/spark:3.5.3

USER root

# Install wget for downloading JARs
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*

# Create directory for custom JARs
RUN mkdir -p /opt/bitnami/spark/jars-custom

WORKDIR /opt/bitnami/spark/jars-custom

# Download Delta Lake 3.3.0 JARs (compatible with Spark 3.5)
RUN wget https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.3.0/delta-spark_2.12-3.3.0.jar && \
    wget https://repo1.maven.org/maven2/io/delta/delta-storage/3.3.0/delta-storage-3.3.0.jar

# Download Unity Catalog Spark connector
RUN wget https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-spark_2.12/0.2.0/unitycatalog-spark_2.12-0.2.0.jar

# Download Hadoop AWS JARs for S3 support (compatible with Spark 3.5)
RUN wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.367/aws-java-sdk-bundle-1.12.367.jar

# Download additional dependencies
RUN wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-common/3.3.4/hadoop-common-3.3.4.jar && \
    wget https://repo1.maven.org/maven2/org/apache/commons/commons-configuration2/2.8.0/commons-configuration2-2.8.0.jar && \
    wget https://repo1.maven.org/maven2/commons-logging/commons-logging/1.2/commons-logging-1.2.jar && \
    wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-auth/3.3.4/hadoop-auth-3.3.4.jar

# Set proper permissions
RUN chown -R 1001:1001 /opt/bitnami/spark/jars-custom

# Copy JARs to main jars directory
RUN cp /opt/bitnami/spark/jars-custom/*.jar /opt/bitnami/spark/jars/

# Verify JARs are present
RUN ls -lh /opt/bitnami/spark/jars/ | grep -E "(delta|hadoop-aws|aws-java-sdk|unitycatalog)"

USER 1001

# Set environment to include custom JARs in classpath
ENV SPARK_EXTRA_CLASSPATH=/opt/bitnami/spark/jars-custom/*:$SPARK_EXTRA_CLASSPATH
