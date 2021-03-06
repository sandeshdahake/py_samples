import mysql.connector
from mysql.connector import errorcode
import product_json
from furl import furl
import re
import locale

add_sub_category = ("INSERT INTO compareBlank.productsubcategories"
                " (CategoryId, Name, Label, MetadataFile, CompareMetadataFile) VALUES"
                " (%(category_id)s, %(category_name)s, %(category_label)s,'test','test' )")

get_sub_category_by_name = ("SELECT id from compareBlank.productsubcategories where Name= %(category_name)s");

add_product= "INSERT INTO compareBlank.products (SubcategoryId, Name, Price, isActive, mspId," \
             " InsertedProperties, IsVisited, ImageInserted, Image, IsBestSeller, Popularity)" \
             " VALUES (%(SubcategoryId)s, %(Name)s, %(Price)s, %(isActive)s, %(mspId)s, %(InsertedProperties)s" \
             ", %(IsVisited)s, %(ImageInserted)s, %(Image)s, %(IsBestSeller)s, %(Popularity)s);"

get_max_msp_id = "select max(mspId)+ 1 from compareBlank.products"

add_store_id="INSERT INTO compareBlank.productwebstores (ProductId, WebstoreLabel, WebstoreName, WebstoreProductId)" \
             " VALUES (%(ProductId)s, %(WebstoreLabel)s, %(WebstoreName)s, %(WebstoreProductId)s)"
add_images="INSERT INTO compareBlank.productimages(ProductId, Url, ZoomImageUrl)" \
           " VALUES (%(ProductId)s, %(Url)s, %(ZoomImageUrl)s )"
add_product_spec="INSERT INTO compareBlank.ProductSpecs(ProductId, category, property, value, columnName, subCategoryId)" \
                 " VALUES (%(ProductId)s, %(category)s,%(property)s, %(value)s, %(columnName)s, %(subCategoryId)s)"
avoid_duplicate_entry = "SELECT count(*) from compareBlank.products WHERE NAME= %s"
call_meta_data_sp="setup_product_table"
setup_up_product_image_url = "UPDATE "

def _get_connection_():
    config = {
       'user': 'root',
       'password': 'root',
       'port':'8889',
       'host': 'localhost',
       'database': 'compare2test',
       'raise_on_warnings': True,
    }
    cnx = mysql.connector.connect(**config)
    return cnx


def save_sub_category(config_cat):
    sub_category_id=0
    cnx = _get_connection_();
    try:
        cursor = cnx.cursor()
        cursor.execute(get_sub_category_by_name, config_cat)
        result = cursor.fetchone()
        if result is None:
#            sub_category_id = cursor.fetchone()[0]
            cursor.execute(add_sub_category,config_cat)
            sub_category_id = cursor.lastrowid
            cnx.commit()
        else:
            sub_category_id = result[0]
    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cursor.close()
        cnx.close()
    return sub_category_id


def _save_product_info(product, sub_category_id, sub_category_name):
    if eval(product['stores']):
        try:
            cnx = _get_connection_();
            cursor = cnx.cursor()
            args = [product['name'].replace(" Price", "")]
            cursor.execute(avoid_duplicate_entry,args)
            count = cursor.fetchone()[0]
            if count == 0:
                print("Processing Product ->",product['name'])
                cursor.execute(get_max_msp_id)
                msp_id = cursor.fetchone()[0]
                product_dict = {'SubcategoryId': sub_category_id ,'Name':product['name'].replace(" Price", ""),
                                'Price':float(product['price'].replace("Rs. ", "").replace(",","")), 'isActive':1, 'mspId':msp_id, 'InsertedProperties':0, 'IsVisited':0 ,
                                'ImageInserted':1, 'Image':'test', 'IsBestSeller':0 , 'Popularity':0}
                cursor.execute(add_product, product_dict)
                product_id = cursor.lastrowid
                stores = eval(product['stores'])
                for store,storeDetails in stores.items():
                    key= store.replace("Amazon.in","amazon");
                    value=storeDetails['url']
                    f = furl(value)
                    pid=value
                    if key.lower()=="amazon" or key.lower() == "snapdeal":
                        pid= f.path.segments[2]
                    elif key.lower() == "flipkart":
                        if 'pid' in f.args:
                            pid= f.args['pid']
                    product_store_dict={'ProductId':product_id,'WebstoreName':key,'WebstoreLabel':key,'WebstoreProductId':pid}
                    cursor.execute(add_store_id, product_store_dict)
                for image in product['images']:
                        image_dict = {'ProductId':product_id,'Url':sub_category_name+'/'+image['path'],'ZoomImageUrl':sub_category_name+'/'+image['path']}
                        cursor.execute(add_images, image_dict)
                product_detail = eval(product['productDetails']);
                for category, sub_category in product_detail.items():
                    for property,value in sub_category.items():
                        # print( product_detail.index(category),"->",category,":", sub_category.index(property),"->", property)
                        product_spcs={'ProductId':product_id, 'category':category, 'property':property, 'value':value, 'columnName':re.sub('\W+', '', property.replace(" ","_")), 'subCategoryId':sub_category_id}
                        cursor.execute(add_product_spec, product_spcs)
                print(product_id);
                cnx.commit()
            else :
                print(product['name'] ,"###############Product Already exist###########")
        except mysql.connector.Error as err:
            cnx.rollback()
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        else:
            cursor.close()
            cnx.close()
        return 0;
    else:
        return 0;

def set_up_main_product_image(sub_category_id):
    try:
        config_cat=[sub_category_id]
        cnx = _get_connection_();
        cursor = cnx.cursor()
        cursor.execute(setup_up_product_image_url, config_cat)
        cnx.commit()
    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
    else:
        cursor.close()
        cnx.close()
    return 0


def _copy_metadata(sub_category_id):
    try:
        config_cat=[sub_category_id]
        cnx = _get_connection_();
        cursor = cnx.cursor()
        cursor.callproc(call_meta_data_sp, config_cat)
        cnx.commit()
    except mysql.connector.Error as err:
        cnx.rollback()
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
    else:
        cursor.close()
        cnx.close()
    return 0
