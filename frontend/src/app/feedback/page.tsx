'use client'
import DetailedQuestionReview from "@/src/components/feedback/DetailedQuestionReview";
import FeedbackSelector from "@/src/components/feedback/FeedbackSelector";
import PerformanceBySkill from "@/src/components/feedback/PerformanceBySkill";
import Loading from "@/src/components/global/Loading";
import PageTitle from "@/src/components/global/PageTitle";
import apiService from "@/src/domain/services/apiService";
import { useEffect, useState } from "react";

export default function page(){
    const [feedback, setFeedback] = useState()
    const [showLoadingFeedback, setShowLoadingFeedback] = useState(false)
    const [selectedExam, setSelectedExam] = useState('')

    async function getNewFeedback(){
        const simulationResults = JSON.parse(
            localStorage.getItem(`simulationResults-${selectedExam}`) || '[]'
        )

        const newFeedback = await apiService.getFeedback(
            selectedExam, 
            simulationResults
        )

        setFeedback(newFeedback)
    }

    useEffect(() => {
        if(showLoadingFeedback){
            getNewFeedback()
        }
    }, [showLoadingFeedback])

    useEffect(() => {
        if(feedback){
            setShowLoadingFeedback(false)
        }
    }, [feedback])

    return (
        <>
        <PageTitle text="Feedback"/>

        <FeedbackSelector selectedExam={selectedExam} setSelectedExam={setSelectedExam} setShowLoadingFeedback={setShowLoadingFeedback}/>

        {feedback ?
            <>
            <PerformanceBySkill feedback={feedback}/>

            <DetailedQuestionReview feedback={feedback}/>
            </>
        : <></>}

        {showLoadingFeedback ?
            <Loading text={'Generating your feedback...'}/>
        : <></>}
        </>
    )
}