from app.utils.db_utils import db_utils
import pymysql

class OrderDatabaseHandler():
    
    @staticmethod
    def update(question_id: str, updated_row: dict):
        print(f"Update Database function")

        mydb = pymysql.connect(**db_utils.json_Reader('app/Credentials/CoreB.json'))
        cursor = mydb.cursor()

        project_id = updated_row['Project ID']
        res_person = updated_row['Reponsible Person']

        query = "UPDATE CoreB_Order SET `Project ID` = %s, `Reponsible Person` = %s WHERE `Index` = %s;"
        cursor.execute(query, (project_id, res_person, question_id))

        # Commit the transaction
        mydb.commit()

        # Close the cursor and connection
        cursor.close()
        mydb.close()
        
        print(f"End of Database function")


    @staticmethod
    def delete():
        raise NotImplementedError("DatabaseHandler for orders not implemented")