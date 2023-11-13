#! /bin/bash

folder=$1
currFolder=$(pwd)/../$folder
echo "======= Process started: $(date) ======="

# Declare an array
declare -a libs
# Check if file ends with newline
newLine=$(tail -n 1 $currFolder/layer.txt)
if [ $newLine == " " ];
then
    echo "####### Adding new line to library file #######"
    # Add newline to end of file
    echo " " >> $currFolder/layer.txt
fi

# Read each line and store in array
while IFS='' read -r lib;
do
    libs+=("$lib")
done <$currFolder/layer.txt
if [ $? -eq 0 ];
then
    echo "####### Successfully fetched list of libraries from file #######"
    echo "Python Libraries: ${libs[@]}"
else
    echo "####### Error fetching libraries from file #######"
    exit 1
fi

for i in ${libs[@]}
do
    echo "####### Creating folder for $i #######"
    mkdir python
    echo "####### Folder created successfully #######"
    echo "####### Installing library into folder #######"
    # Download py library into folder
    pip3 install -t python $i
    if [ $? -eq 0 ];
    then
        echo "####### Library files downloaded into folder: $i #######"
    else
        echo "####### Error in downloading library: $i #######"
        exit 1
    fi
    echo "####### Zipping folder for upload process to S3 #######"
    zip -r python.zip python
    if [ $? -eq 0 ];
    then
        echo "####### Folder has been zipped successfully #######"
    else
        echo "####### Error in zipping folder #######"
        exit 1
    fi
    echo "####### Uploading file to S3 bucket #######"
    bucket=$2
    aws s3 cp $currFolder/../aws_deployments/python.zip s3://$bucket/
    if [ $? -eq 0 ];
    then
        echo "####### Zip file has been successfully uploaded to S3 #######"
    else
        echo "####### Error in uploading zip file to S3 #######"
        exit 1
    fi
    rm -rf python
    rm python.zip
    echo "####### Creating lambda layer for $i #######"
    aws lambda publish-layer-version \
        --layer-name $i \
        --content S3Bucket=$bucket,S3Key=python.zip \
        --compatible-runtimes python3.10 \
        --compatible-architectures "x86_64"
    if [ $? -eq 0 ];
    then
        echo "####### Lambda layer has been created for $i #######"
    else
        echo "####### Error in creating lambda layer #######"
        exit 1
    fi
    echo "####### Renaming file in s3 #######"
    aws s3 mv s3://$bucket/python.zip s3://$bucket/$i.zip
    if [ $? -eq 0 ];
    then
        echo "####### File has been renamed to $i.zip #######"
    else
        echo "####### Error in renaming file in s3 #######"
        exit 1
    fi
done

echo "======= Process ended: $(date) ======="
