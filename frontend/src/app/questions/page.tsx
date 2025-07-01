import PageTitle from "@/src/components/global/PageTitle";
import QuestionsForm from "@/src/components/questions/QuestionsForm";

export default function page(){
    return(
        <>
        <PageTitle text="Generate Diagnostic Questions"/>

        <QuestionsForm/>
        </>
    )
}