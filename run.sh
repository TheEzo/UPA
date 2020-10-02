#!/bin/bash

help()
{
    echo ""
    echo "UPA Project"
    echo "Authors:"
    echo "  Petr Kapoun <xkapou04@stud.fit.vutbr.cz>"
    echo "  Pavel Novacek <xnovac16@stud.fit.vutbr.cz>"
    echo "  Tomas Willaschek <xwilla00@stud.fit.vutbr.cz>"
    echo ""
    echo "Usage: ./run.sh [-h]"
    echo "  -h     prints help"
    echo "  -b     forces container to rebuild"
    echo "  -sqlr  forces MySQL db to recreate"
    echo "  -esr   forces Elastic Search db to recreate"
    echo ""
}

SHOULD_BUILD="0"
ES_RECREATE="0"
SQL_RECREATE="0"

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    case $PARAM in
        -h | --help)
            help
            exit
            ;;
        -b | --build)
            SHOULD_BUILD="1"
            ;;
        -esr | --es-recreate)
            ES_RECREATE="1"
            ;;

        -sqlr | --sql-recreate)
            SQL_RECREATE="1"
            ;;
        *)
            echo "ERROR: unknown parameter \"$PARAM\""
            help
            exit 1
            ;;
    esac
    shift
done

DOCKER_IMAGE_PREFIX="upa"

if [ $ES_RECREATE = "1" ]; then
    db_name="${DOCKER_IMAGE_PREFIX}_es_db"

    found=`docker volume list | grep -c -x -E "^local\s+${db_name}$"`

    if [ $found -eq 1 ]; then 
        docker-compose -p $DOCKER_IMAGE_PREFIX down
        docker volume remove $db_name
    fi
fi

if [ $SQL_RECREATE = "1" ]; then
    db_name="${DOCKER_IMAGE_PREFIX}_mysql_db"

    found=`docker volume list | grep -c -x -E "^local\s+${db_name}$"`

    if [ $found -eq 1 ]; then 
        docker-compose -p $DOCKER_IMAGE_PREFIX down
        docker volume remove $db_name
    fi
fi

if [ $SHOULD_BUILD = "1" ]; then
    docker-compose -p $DOCKER_IMAGE_PREFIX up --build
else
    docker-compose -p $DOCKER_IMAGE_PREFIX up
fi

#clean() {
#    docker-compose -p $DOCKER_IMAGE_PREFIX down
#}