'use client'
import AskForm from "@/src/components/ask/AskForm";
import QuestionAnswer from "@/src/components/ask/QuestionAnswer";
import Loading from "@/src/components/global/Loading";
import PageTitle from "@/src/components/global/PageTitle";
import { useEffect, useState } from "react";

export default function page(){
    const [questionAnswer, setQuestionAnswer] = useState('')
    const [showLoading, setShowLoading] = useState(false)
    
    useEffect(() => {
        setShowLoading(false)
    }, [questionAnswer])

    return (
        <>
        <PageTitle text="Ask a Question"/>

        <AskForm setQuestionAnswer={setQuestionAnswer} setShowLoading={setShowLoading}/>

        {questionAnswer ?
            <QuestionAnswer answer={questionAnswer}/>
        : <></>}

        {showLoading ?
            <Loading text={'Generating your answer...'}/>
        : <></>}
        </>
    )
}